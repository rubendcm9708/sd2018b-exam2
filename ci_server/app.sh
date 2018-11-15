export LANG=en_US.utf8
export PYTHONPATH=$PYTHONPATH:`pwd`
export FLASK_ENV=development
connexion run /code/gm_analytics/swagger/indexer.yaml --debug -p 8088
