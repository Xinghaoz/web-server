import BaseHTTPServer
import sys, os
import subprocess

class ServerException(Exception):
    ''' Server Inner error '''
    pass

# Base case class
class base_case(object):
    def handle_file(self, handler, full_path):
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
            handler.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(full_path, msg)
            handler.handle_error(msg)

    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    def test(self, handler):
        assert False, 'Not implemented.'

    def act(self, handler):
        assert False, 'Not implemented'


class case_no_file(base_case):
    '''The path doesn't exist'''

    def test(self, handler):
        return not os.path.exists(handler.full_path)

    def act(self, handler):
        raise ServerExceptino("'{0}' not found".format(handler.path))

class case_existing_file(base_case):
    '''This path is a file'''

    def test(self, handler):
        return os.path.isfile(handler.full_path)

    def act(self, handler):
        handler.handle_file(handler.full_path)

class case_always_fail(base_case):
    '''When none of the cases apply'''

    def test(self, handler):
        return True

    def act(self, handler):
        raise ServerException("Unknow object '{0}'".format(handler.path))

class case_directory_index_file(base_case):

    def test(self, handler):
        return os.path.isdir(handler.full_path) and os.path.isfile(self.index_path(handler))

    def act(self, handler):
        handler.handle_file(self.index_path(handler))

class case_cgi_file(base_case):
    ''' Process the script '''

    def test(self, handler):
        return os.path.isfile(handler.full_path) and handler.full_path.endswith('.py')

    def act(self, handler):
        handler.run_cgi(handler.full_path)

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    ''' Handle the requests and return the page '''

    Page =  '''\
            <html>
            <body>
            <table>
            <tr> <td>Header</td>        <td>Value</td>          </tr>
            <tr> <td>Date and time</td> <td>{date_time}</td>    </tr>
            <tr> <td>Client host</td>   <td>{client_host}</td>  </tr>
            <tr> <td>Client port</td>   <td>{client_port}</td>  </tr>
            <tr> <td>Command</td>       <td>{command}</td>      </tr>
            <tr> <td>Path</td>          <td>{path}</td>         </tr>
            </table>
            </body>
            </html>
            '''




    Cases = [case_no_file(),
             case_existing_file(),
             case_directory_index_file(),
             case_cgi_file(),
             case_always_fail()]
    # Handle the GET request
    def do_GET(self):

        try:
            # Completed path
            self.full_path = os.getcwd() + self.path

            for case in self.Cases:
                handler = case

                if handler.test(self):
                    handler.act(self)
                    break


            '''
            # If not exist
            if not os.path.exists(full_path):
                raise ServerException("'{0}' not found".format(self.path))

            # If the path is a file
            elif os.path.isfile(full_path):
                self.handle_file(full_path)

            # If not a file
            else:
                raise ServerException("Unknow object '{0}'".format(self.path))
            '''

        except Exception as msg:
            self.handle_error(msg)

        page = self.create_page()
        self.send_content(page)

        """
        self.send_response(200)
        self.send_header("Content-Type", "text/html") # Can run without it
        self.send_header("Content-Length", str(len(self.Page))) # Can run without it
        self.end_headers()
        self.wfile.write(self.Page)
        """


    def create_page(self):
        values = {
            'date_time' : self.date_time_string(),
            'client_host' : self.client_address[0],
            'client_port' : self.client_address[1],
            'command' : self.command,
            'path' : self.path
        }
        page = self.Page.format(**values)
        return page


    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def handle_file(self, full_path):
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
            self.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(self.path, msg)
            self.handle_error(msg)

    Error_Page = """\
            <html>
            <body>
            <h1>Error accessing {path}</h1>
            <p>{msg}</p>
            </body>
            </html>
            """
    def handle_error(self, msg):
        content = self.Error_Page.format(path=self.path, msg=msg)
        self.send_content(content, 404)

    def run_cgi(self, full_path):
        data = subprocess.check_output(["python", handler.full_path])
        self.send_content(data)



if __name__ == '__main__':
    serverAddress = ('', 8080)
    server = BaseHTTPServer.HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()
