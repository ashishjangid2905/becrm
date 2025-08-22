from waitress import serve
from becrm.wsgi import application  # Replace 'myproject' with your actual project name

serve(application, host='127.0.0.1', port=8000)
