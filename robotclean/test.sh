# initialisation
curl -X POST http://127.0.0.1:8000/api/setup/ \
     -H "Content-Type: application/json" \
     -d '{"nr": 4, "nd": 6, "i": 10, "j": 5}'

# récupération de la grille
curl http://127.0.0.1:8000/api/grid/
