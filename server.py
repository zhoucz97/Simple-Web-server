from http.server import BaseHTTPRequestHandler, HTTPServer
import sys, os
import subprocess


class ServerException(Exception):
    '''服务器内部错误'''
    pass

#-----------------------------------------------------------

class base_case(object):
    '''条件处理基类'''
    
    def handle_file(self, handler, full_path):
        try:
            # 获取相应HTML文件的内容
            with open(full_path, 'rb') as reader:
                content = reader.read()
            handler.send_content(content)   # 发送数据到客户端
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(full_path, msg)
            handler.handle_error(msg) 
    
    def index_path(self, handler):  # 返回默认页面完整路径
        return os.path.join(handler.full_path, 'index.html')

    # 要求子类必须实现这两个接口
    def test(self, handler):
        # 条件为False时触发异常
        assert False, 'Not implemented.'
    
    def act(self, handler):
        assert False, 'Not implemented.'

#-----------------------------------------------------------

class case_no_file(base_case):
    '''文件或目录不存在'''
    def test(self, handler):  # 测试该路径是否存在
        return not os.path.exists(handler.full_path)
    
    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path))


class case_cgi_file(base_case):
    # 可执行脚本
    def run_cgi(self, handler):
        # check_output执行一个指定的命令并将执行结果以一个字节字符串的形式返回。
        data = subprocess.check_output(["python", handler.full_path],shell=False)
        handler.send_content(data)

    def test(self, handler):
        return os.path.isfile(handler.full_path) and handler.full_path.endswith('.py')

    def act(self, handler):
        # 运行脚本文件
        self.run_cgi(handler)


class case_existing_file(base_case):
    '''该路径是文件'''
    def test(self, handler):
        return os.path.isfile(handler.full_path)
    
    def act(self, handler):
        self.handle_file(handler, handler.full_path)


class case_directory_index_file(base_case):
    '''访问根目录时返回index.html'''
    #判断目标路径是否是目录&&目录下是否有index.html
    def test(self, handler):
        return os.path.isdir(handler.full_path) and os.path.isfile(self.index_path(handler))

    #响应index.html的内容
    def act(self, handler):
        self.handle_file(handler, self.index_path(handler))


class case_always_fail(base_case):
    '''所有情况都不符合时的默认处理类'''
    def test(self, handler):
        return True
    
    def act(self, handler):
        raise ServerException("Unknown object '{0}'".format(handler.path))

#-----------------------------------------------------------------

class RequestHandler(BaseHTTPRequestHandler):
    '''处理请求并返回页面'''
    # 错误页面模板
    Error_Page = """\
        <html>
        <body>
        <h1>Error accessing {path}</h1>
        <p>{msg}</p>
        </body>
        </html>
        """
    Cases = [case_no_file(), 
                case_cgi_file(),
                case_existing_file(),  
                case_directory_index_file(), 
                case_always_fail()]      

    # 处理一个GET请求
    def do_GET(self):
        try:
            self.full_path = os.getcwd() + self.path # 文件完整路径
            # 所有可能的情况(3种)
            for case in self.Cases:
                # 如果满足该类
                if case.test(self):
                    case.act(self)
                    break
        except Exception as msg:    # 处理异常
            self.handle_error(msg)

    
    def handle_error(self, msg):
        # 错误处理
        content = self.Error_Page.format(path=self.path, msg=msg)
        self.send_content(content.encode('utf-8'), 404)


    def send_content(self, content, status=200):
        # 发送数据到客户端
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


    def handle_file(self, full_path):
        # 文件处理
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
                self.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(self.path, msg)
            self.handle_error(msg)

    

if __name__ == '__main__':
    print('success')
    serverAddress = ('', 8080)
    server = HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()