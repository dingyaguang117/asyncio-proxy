import asyncio


class ProxyServer(object):

    METHODS = [b'CONNECT', b'GET', b'POST', b'DELETE', b'PUT', b'OPTIONS']

    async def parse_header(self, reader):
        data, headers = b'', {}

        line = await reader.readline()
        items = line.split(b' ')

        if len(items) < 2:
            return data, headers

        _method = items[0]
        if _method not in self.METHODS:
            return data, headers
        headers['_method'] = _method
        data = data + line

        while True:
            line = await reader.readline()
            data = data + line
            if line == b'\r\n' or line == b'':
                break
            try:
                k, v = line.split(b':', 1)
                headers[k] = v.strip()
            except:
                pass

        headers['_host'] = headers[b'Host']
        if headers['_host'].find(b':') != -1:
            headers['_host'], headers['_port'] = headers['_host'].split(b':')
            headers['_port'] = int(headers['_port'])
        else:
            headers['_port'] = 80
        return data, headers

    def client_close(self, reader, writer):
        writer.close()

    async def create_connection(self, host, port):
        try:
            reader, writer = await asyncio.open_connection(host, port)
        except Exception as e:
            print('连接服务器出错：', host, port)
            print(e)
            return None, None
        print('success create connection ', host, port)
        return reader, writer

    async def transport(self, name, reader, writer):
        while True:
            data = await reader.read(1024)
            if not data:
                print('break:', name)
                writer.close()
                break
            writer.write(data)

    async def client_connected(self, reader, writer):
        data, headers = await self.parse_header(reader)
        # print(headers)
        if not headers:
            print('invalid http request')
            self.client_close(reader, writer)
            return

        remote_reader, remote_writer = await self.create_connection(headers['_host'], headers['_port'])
        if not remote_writer or not remote_reader:
            self.client_close(reader, writer)
            return

        if headers['_method'] == b'CONNECT':
            writer.write(b'HTTP/1.1 200 OK\r\n\r\n')
        else:
            remote_writer.write(data)

        asyncio.get_event_loop().create_task(self.transport(headers[b'Host'] + b' request', reader, remote_writer))
        asyncio.get_event_loop().create_task(self.transport(headers[b'Host'] + b' response', remote_reader, writer))

    async def serve_forever(self, host, port):
        # asyncio.get_event_loop().create_task(self.display_info())
        server = await asyncio.start_server(self.client_connected, host, port)
        await server.serve_forever()

    async def display_info(self):
        while True:
            print('all tasks:')
            print(len(asyncio.all_tasks()))
            await asyncio.sleep(3)

    def run(self, host, port):
        asyncio.run(server.serve_forever(host, port))

if __name__ == '__main__':
    server = ProxyServer()
    server.run('127.0.0.1', 8008)
