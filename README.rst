carte-departements
==================

Ce dépôt comporte quelques scripts pour facilement générer un fond de carte
pour la France métropolitaine (Corse comprise) et placer des icônes sur une
liste de ville (identifiée par les codes INSEE des villes). Voir le fichier
inclus villes.json pour un exemple de fichier à générer.

Usage :

.. code-block:: bash

    $ pipenv install
    $ pipenv run doit villes=mes_villes.json width=1000 height=1000 svg=carte.svg

