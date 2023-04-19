import asyncio
import asyncssh


class SSHClient:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    async def upload_file(self, local_path, remote_path):
        async with asyncssh.connect(self.host, username=self.username, password=self.password) as conn:
            async with conn.start_sftp() as sftp:
                await sftp.put(local_path, remote_path)

    async def read_file(self, remote_path):
        async with asyncssh.connect(self.host, username=self.username, password=self.password) as conn:
            async with conn.start_sftp() as sftp:
                with await sftp.open(remote_path) as f:
                    content = await f.read()
                    return content

    async def delete_file(self, remote_path):
        async with asyncssh.connect(self.host, username=self.username, password=self.password) as conn:
            async with conn.start_sftp() as sftp:
                await sftp.remove(remote_path)


async def main():
    client = SSHClient('localhost', 'user', 'password')

    # Upload file
    await client.upload_file('/path/to/local/file', '/remote/path')

    # Read file
    content = await client.read_file('/remote/path')
    print(content)

    # Delete file
    await client.delete_file('/remote/path')

asyncio.run(main())
