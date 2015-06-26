from livereload import Server

server = Server()

server.watch('*')
server.watch('css/*')

server.serve()
