import json
import os
from pathlib import Path

from doit import get_var
from doit.tools import config_changed

BASE_DIR = Path(__file__).parent
BUILD_DIR = BASE_DIR / "build"

VILLES_FICHIER = get_var("villes", BASE_DIR / "villes.json")
SVG_FILE = get_var("svg", BASE_DIR / "carte.svg")
WIDTH = get_var("width", 1000)
HEIGHT = get_var("height", 1000)

FILTER_IDF = (
    '["75", "77", "78", "91", "92", "93", "94", "95"].includes({0}.properties.code)'
)
FILTER_CORSE = '["2A", "2B"].includes({0}.properties.code)'
FILTER_RESTE = f"!({FILTER_IDF} || {FILTER_CORSE})"

os.environ["PATH"] = (
    str(BASE_DIR / "node_modules" / ".bin") + os.pathsep + os.environ["PATH"]
)

with open(VILLES_FICHIER) as f:
    VILLES = json.load(f)


PROJECTION = "d3.geoConicConformal().parallels([44, 49]).rotate([-3, 0])"


def ensure_dir(dir):
    return ["mkdir", "-p", dir]


def task_create_villes_geojson():
    input = BASE_DIR / "communes-centroid.ndjson"
    output = BUILD_DIR / "villes.geojson"
    tableau_liste = ",".join(f'"{v}"' for v in VILLES)
    return {
        "file_dep": [VILLES_FICHIER, input],
        "targets": [output],
        "actions": [
            ensure_dir(BUILD_DIR),
            f"ndjson-filter '[{tableau_liste}].includes(d.properties.insee)' < {input} "
            "| ndjson-reduce 'p.features.push(d), p' '{type:\"FeatureCollection\",features:[]}'"
            f"> {output}",
        ],
    }


def task_projection():
    departements = "departements-version-simplifiee.geojson"
    projected_departements = BUILD_DIR / "projected-departements.geojson"
    yield {
        "name": "departements",
        "file_dep": [departements],
        "targets": [projected_departements],
        "actions": [
            f"geoproject '{PROJECTION}' < '{departements}' > '{projected_departements}'"
        ],
        "uptodate": [config_changed(PROJECTION)],
    }

    villes = BUILD_DIR / "villes.geojson"
    projected_villes = BUILD_DIR / "projected-villes.geojson"
    yield {
        "name": "villes",
        "file_dep": [villes],
        "targets": [projected_villes],
        "actions": [f"geoproject '{PROJECTION}' < '{villes}' > '{projected_villes}'"],
        "uptodate": [config_changed(PROJECTION)],
    }


def show(s):
    print(s)


def task_creer_topologie():
    departements = BUILD_DIR / "projected-departements.geojson"
    villes = BUILD_DIR / "projected-villes.geojson"

    return {
        "file_dep": [departements, villes],
        "targets": [BUILD_DIR / "topology.json"],
        "actions": [
            f"""
            geo2topo "metropoleInt={departements}" "villes={villes}" \
            | topomerge -f '{FILTER_IDF.format("d")}' "idfExt=metropoleInt" \
            | topomerge --mesh -f '(a != b) && {FILTER_IDF.format("a")} && {FILTER_IDF.format("b")}' "idfInt=metropoleInt" \
            | topomerge -f '{FILTER_CORSE.format("d")}' "corseExt=metropoleInt" \
            | topomerge --mesh -f '(a != b) && {FILTER_CORSE.format("a")} && {FILTER_CORSE.format("b")}' "corseInt=metropoleInt" \
            | topomerge -f '{FILTER_RESTE.format("d")}' "metropoleExt=metropoleInt" \
            | topomerge --mesh -f '(a != b) && {FILTER_RESTE.format("a")} && {FILTER_RESTE.format("b")}' "metropoleInt=metropoleInt" \
            > %(targets)s
        """.strip()
        ],
    }


def task_creer_carte():
    topology = BUILD_DIR / "topology.json"

    return {
        "file_dep": [topology],
        "targets": [SVG_FILE],
        "actions": [
            f"node createSVG.mjs --width {WIDTH} --height {HEIGHT} '{topology}' > '{SVG_FILE}'"
        ],
        "uptodate": [config_changed({"width": WIDTH, "height": HEIGHT})],
    }
