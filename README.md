API для системы опросов пользователей.
-----------

Сервис запускается с помощью команд:

 Сборка
 **docker-compose up --build**
 
 Создание администратора и суперюзера
 **docker-compose run --rm   app python manage.py start_server**  
 
 Логин и пароль администратора указаны в настройках 


Документация открывается по адресу 
**127.0.0.1:8000/api/swagger/**. 

Тесты запускаются командой 
**docker-compose run --rm   app python manage.py test**

