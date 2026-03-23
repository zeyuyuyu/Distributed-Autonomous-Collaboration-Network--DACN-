import asyncio
from typing import Dict, Set
import json
import logging

class NetworkManager:
    def __init__(self, host: str = '0.0.0.0', port: int = 8000):
        self.host = host
        self.port = port
        self.peers: Dict[str, dict] = {}
        self.active_connections: Set[str] = set()
        self.logger = logging.getLogger('network')

    async def start_server(self):
        server = await asyncio.start_server(
            self.handle_connection, self.host, self.port
        )
        self.logger.info(f'Network server started on {self.host}:{self.port}')
        await server.serve_forever()

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer_addr = writer.get_extra_info('peername')
        peer_id = f'{peer_addr[0]}:{peer_addr[1]}'
        
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                    
                message = json.loads(data.decode())
                await self.process_message(message, peer_id)
                
        except Exception as e:
            self.logger.error(f'Error handling connection from {peer_id}: {str(e)}')
        finally:
            self.remove_peer(peer_id)
            writer.close()
            await writer.wait_closed()

    async def connect_to_peer(self, peer_host: str, peer_port: int):
        try:
            reader, writer = await asyncio.open_connection(peer_host, peer_port)
            peer_id = f'{peer_host}:{peer_port}'
            
            self.peers[peer_id] = {
                'host': peer_host,
                'port': peer_port,
                'reader': reader,
                'writer': writer
            }
            self.active_connections.add(peer_id)
            
            # Send hello message
            await self.send_message(peer_id, {
                'type': 'hello',
                'version': '1.0.0',
                'capabilities': ['sync', 'discovery']
            })
            
            self.logger.info(f'Successfully connected to peer {peer_id}')
            return True
            
        except Exception as e:
            self.logger.error(f'Failed to connect to {peer_host}:{peer_port}: {str(e)}')
            return False

    async def send_message(self, peer_id: str, message: dict):
        if peer_id not in self.peers:
            raise ValueError(f'Unknown peer {peer_id}')
            
        writer = self.peers[peer_id]['writer']
        data = json.dumps(message).encode()
        writer.write(data)
        await writer.drain()

    async def process_message(self, message: dict, peer_id: str):
        msg_type = message.get('type')
        
        if msg_type == 'hello':
            self.logger.info(f'Received hello from {peer_id}')
            # Handle peer capabilities and version
            peer_version = message.get('version')
            peer_capabilities = message.get('capabilities', [])
            self.peers[peer_id]['version'] = peer_version
            self.peers[peer_id]['capabilities'] = peer_capabilities
            
        elif msg_type == 'discover':
            # Share known peers
            await self.send_message(peer_id, {
                'type': 'peers',
                'peers': [
                    {'host': p['host'], 'port': p['port']}
                    for p in self.peers.values()
                    if p['host'] != self.host or p['port'] != self.port
                ]
            })

    def remove_peer(self, peer_id: str):
        if peer_id in self.peers:
            del self.peers[peer_id]
        self.active_connections.discard(peer_id)
        self.logger.info(f'Peer {peer_id} disconnected')

    async def broadcast(self, message: dict):
        for peer_id in list(self.active_connections):
            try:
                await self.send_message(peer_id, message)
            except Exception as e:
                self.logger.error(f'Failed to broadcast to {peer_id}: {str(e)}')
                self.remove_peer(peer_id)
