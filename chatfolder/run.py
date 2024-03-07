from app import create_app, socketio, db

app = create_app()

# Стоврення таблиць в контексті застосунка
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True)
