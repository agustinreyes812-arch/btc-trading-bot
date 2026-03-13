import asyncio
import websockets
import json
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinanceOrderBookBot:
    def __init__(self, symbol: str = "btcusdt"):
        self.symbol = symbol.lower()
        self.base_ws = "wss://stream.binance.com:9443/ws"
        self.base_rest = "https://api.binance.com/api/v3"
        self.order_book = {
            "bids": {},  # Dict[price, quantity]
            "asks": {},  # Dict[price, quantity]
            "last_update_id": 0
        }
        self.event_buffer = []
        self.synchronized = False
        
    async def get_snapshot(self, limit: int = 100) -> Dict:
        """Obtener snapshot inicial del libro de órdenes"""
        url = f"{self.base_rest}/depth"
        params = {
            "symbol": self.symbol.upper(),
            "limit": limit
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Snapshot obtenido - LastUpdateId: {data['lastUpdateId']}")
                        return data
                    else:
                        error_data = await response.text()
                        logger.error(f"❌ Error {response.status}: {error_data}")
                        
                        # Manejar errores específicos [citation:6]
                        if response.status == 429:
                            wait_time = int(response.headers.get('Retry-After', 60))
                            logger.warning(f"⏳ Rate limit excedido. Esperar {wait_time}s")
                            await asyncio.sleep(wait_time)
                            return await self.get_snapshot(limit)
                        elif response.status >= 500:
                            logger.warning("⚠️ Error del servidor Binance, reintentando...")
                            await asyncio.sleep(5)
                            return await self.get_snapshot(limit)
                        return None
            except Exception as e:
                logger.error(f"❌ Excepción en snapshot: {e}")
                return None
                
    def apply_snapshot(self, snapshot: Dict):
        """Aplicar snapshot inicial al libro local"""
        self.order_book["last_update_id"] = snapshot["lastUpdateId"]
        
        # Procesar bids
        self.order_book["bids"] = {}
        for bid in snapshot["bids"]:
            price = float(bid[0])
            quantity = float(bid[1])
            if quantity > 0:
                self.order_book["bids"][price] = quantity
                
        # Procesar asks
        self.order_book["asks"] = {}
        for ask in snapshot["asks"]:
            price = float(ask[0])
            quantity = float(ask[1])
            if quantity > 0:
                self.order_book["asks"][price] = quantity
                
        logger.info(f"📊 Libro inicial: {len(self.order_book['bids'])} bids, {len(self.order_book['asks'])} asks")
        
    def apply_depth_update(self, update: Dict):
        """Aplicar una actualización de profundidad al libro local"""
        # Verificar sincronización [citation:8]
        if not self.synchronized:
            # Primer evento después del snapshot
            if update["U"] <= self.order_book["last_update_id"] <= update["u"]:
                self.synchronized = True
                logger.info("✅ Libro sincronizado")
            else:
                # Descartar eventos viejos [citation:8]
                if update["u"] < self.order_book["last_update_id"]:
                    return
                else:
                    logger.warning("⚠️ Necesita resincronización")
                    asyncio.create_task(self.resync())
                    return
        else:
            # Verificar continuidad [citation:8]
            if update["pu"] != self.order_book.get("last_u", 0):
                logger.warning(f"⚠️ Cadena rota: esperaba {self.order_book.get('last_u')}, recibió {update['pu']}")
                asyncio.create_task(self.resync())
                return
        
        # Aplicar cambios en bids [citation:7]
        for bid in update["b"]:
            price = float(bid[0])
            quantity = float(bid[1])
            
            if quantity > 0:
                self.order_book["bids"][price] = quantity
            else:
                # Si quantity = 0, eliminar el nivel de precio [citation:8]
                self.order_book["bids"].pop(price, None)
                
        # Aplicar cambios en asks
        for ask in update["a"]:
            price = float(ask[0])
            quantity = float(ask[1])
            
            if quantity > 0:
                self.order_book["asks"][price] = quantity
            else:
                self.order_book["asks"].pop(price, None)
                
        # Guardar último update ID para validación de cadena [citation:8]
        self.order_book["last_u"] = update["u"]
        
        # Analizar en busca de órdenes falsas
        self.detect_spoofing()
        
    def detect_spoofing(self):
        """Detectar posibles órdenes falsas (spoofing)"""
        if len(self.order_book["asks"]) < 5 or len(self.order_book["bids"]) < 5:
            return
            
        # Ordenar bids (mayor a menor) y asks (menor a mayor)
        sorted_bids = sorted(self.order_book["bids"].items(), reverse=True)
        sorted_asks = sorted(self.order_book["asks"].items())
        
        best_bid = sorted_bids[0][0] if sorted_bids else 0
        best_ask = sorted_asks[0][0] if sorted_asks else 0
        spread = best_ask - best_bid
        
        # Detectar órdenes anormalmente grandes en los niveles 3-5 [citation:1]
        # que podrían ser falsas (spoofing)
        
        # Lado de venta (asks)
        large_asks = []
        for i, (price, qty) in enumerate(sorted_asks[:5]):
            avg_qty = sum(q for _, q in sorted_asks[:5]) / len(sorted_asks[:5])
            if qty > avg_qty * 3:  # Orden 3x más grande que el promedio
                large_asks.append((price, qty, i+1))
                
        # Lado de compra (bids)
        large_bids = []
        for i, (price, qty) in enumerate(sorted_bids[:5]):
            avg_qty = sum(q for _, q in sorted_bids[:5]) / len(sorted_bids[:5])
            if qty > avg_qty * 3:
                large_bids.append((price, qty, i+1))
        
        # Analizar patrones de spoofing
        if large_asks:
            for price, qty, level in large_asks:
                # Si hay una orden de venta grande en nivel 2-4 y el spread es pequeño
                if level >= 2 and level <= 4 and spread < best_ask * 0.001:  # spread < 0.1%
                    logger.warning(f"🚨 POSIBLE SPOOFING: Venta grande en nivel {level}: {qty:.4f} @ {price:.2f}")
                    
        if large_bids:
            for price, qty, level in large_bids:
                if level >= 2 and level <= 4 and spread < best_ask * 0.001:
                    logger.warning(f"🚨 POSIBLE SPOOFING: Compra grande en nivel {level}: {qty:.4f} @ {price:.2f}")
        
        # Mostrar top 3 del libro
        self.display_order_book_top(sorted_bids[:3], sorted_asks[:3])
        
    def display_order_book_top(self, top_bids: List, top_asks: List):
        """Mostrar los mejores niveles del libro"""
        print(f"\n{'='*50}")
        print(f"🕐 {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        print(f"{'ASKS (Venta)':>30}")
        for price, qty in reversed(top_asks):  # Invertir para mostrar mejor ask arriba
            print(f"{price:>15.2f} | {qty:>10.4f}")
        print(f"{'-'*30}")
        print(f"{'BIDS (Compra)':>30}")
        for price, qty in top_bids:
            print(f"{price:>15.2f} | {qty:>10.4f}")
        print(f"{'='*50}")
        
    async def resync(self):
        """Resincronizar el libro de órdenes"""
        logger.info("🔄 Resincronizando libro...")
        self.synchronized = False
        snapshot = await self.get_snapshot(100)
        if snapshot:
            self.apply_snapshot(snapshot)
            self.event_buffer = []
            
    async def run(self):
        """Ejecutar el bot de WebSocket"""
        # Obtener snapshot inicial
        snapshot = await self.get_snapshot(100)
        if not snapshot:
            logger.error("❌ No se pudo obtener snapshot inicial")
            return
            
        self.apply_snapshot(snapshot)
        
        # Conectar WebSocket
        stream = f"{self.symbol}@depth@100ms"  # Actualización cada 100ms [citation:7]
        ws_url = f"{self.base_ws}/{stream}"
        
        while True:
            try:
                async with websockets.connect(ws_url) as websocket:
                    logger.info(f"✅ WebSocket conectado: {stream}")
                    
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            self.apply_depth_update(data)
                        except json.JSONDecodeError:
                            logger.error(f"❌ JSON inválido: {message[:100]}")
                        except Exception as e:
                            logger.error(f"❌ Error procesando mensaje: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("⚠️ Conexión cerrada, reconectando en 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ Error en WebSocket: {e}")
                await asyncio.sleep(5)

async def main():
    bot = BinanceOrderBookBot("btcusdt")
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot detenido por el usuario")
