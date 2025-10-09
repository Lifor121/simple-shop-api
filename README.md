# readme

Building the image and applying migrations (upon schema/dependency changes):
```docker-compose up --build db alembic_migrator```

Starting the main application and workers:
```docker-compose up --build -d app worker```

(works only for linux i guess)
