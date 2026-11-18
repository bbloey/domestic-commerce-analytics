"""Start the complete local dashboard; keep this process running."""
import threading, webbrowser
import server
if __name__=='__main__':
    if hasattr(server,'ensure_initial_runtime'): server.ensure_initial_runtime()
    threading.Timer(1.5,lambda:webbrowser.open('http://127.0.0.1:8867/#sources')).start()
    server.app.run(host='127.0.0.1',port=8867,debug=False,threaded=True)
