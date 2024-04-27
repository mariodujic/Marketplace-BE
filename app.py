import os

from dotenv import load_dotenv
from app.database.main import create_users_table

from app import create_app

# Load environment variables
load_dotenv()

app = create_app()
create_users_table()

if __name__ == '__main__':
    app.run(debug=os.getenv('DEBUG', 'False') == 'True')
