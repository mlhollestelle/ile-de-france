import synpp
import os
import hashlib, gzip
from . import testdata
import sqlite3

def hash_sqlite_db(path):
    """
    Hash SQLite database file from its dump.

    As binary files of SQLite can be a different between OS (maybe due to a
    difference between the implementations of the driver) and only content
    matter, hashing the dump of the database is more relevant.
    """
    con = sqlite3.connect(path)
    hash = hashlib.md5()
    for line in con.iterdump():
        encoded = (line + "\n").encode()
        hash.update(encoded)
    con.close()
    return hash.hexdigest()


def hash_file(file):
    hash = hashlib.md5()

    # Gzip saves time stamps, so the gzipped files are NOT the same!
    opener = lambda: open(file, "rb")

    if file.endswith(".gz"):
        opener = lambda: gzip.open(file)

    with opener() as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)

    f.close()
    return hash.hexdigest()

def test_determinism(tmpdir):
    data_path = str(tmpdir.mkdir("data"))
    testdata.create(data_path)

    for index in range(2):
        _test_determinism(index, data_path, tmpdir)

def _test_determinism(index, data_path, tmpdir):
    print("Running index %d" % index)

    cache_path = str(tmpdir.mkdir("cache_%d" % index))
    output_path = str(tmpdir.mkdir("output_%d" % index))
    config = dict(
        data_path = data_path, output_path = output_path,
        regions = [10, 11], sampling_rate = 1.0, hts = "entd",
        random_seed = 1000, processes = 1,
        secloc_maximum_iterations = 10,
        maven_skip_tests = True
    )

    stages = [
        dict(descriptor = "synthesis.output"),
    ]

    synpp.run(stages, config, working_directory = cache_path)

    REFERENCE_CSV_HASHES = {
        "ile_de_france_activities.csv":     "dcf8e08e9f238c90bff0298048251dac",
        "ile_de_france_households.csv":     "fa08f930689b27f9772c79d35075960d",
        "ile_de_france_persons.csv":        "ed87e2b6dfd2a9914d5fc7b2bf6d52d3",
        "ile_de_france_trips.csv":          "63425b21b452b65418db6f6d987a0162",
    }

    REFERENCE_GPKG_HASHES = {
        "ile_de_france_activities.gpkg":    "f9e519cb5665c314431bcd16bbb8b1b8",
        "ile_de_france_commutes.gpkg":      "2e752795b7cd8e0cd4c8d32e736e455e",
        "ile_de_france_homes.gpkg":         "6f028d84944df9c4ae9342a47a932074",
        "ile_de_france_trips.gpkg":         "c5fdcff9416563823dd824c2a8ea85bd",
    }

    generated_csv_hashes = {
        file: hash_file("%s/%s" % (output_path, file)) for file in REFERENCE_CSV_HASHES.keys()
    }

    generated_gpkg_hashes = {
        file: hash_sqlite_db("%s/%s" % (output_path, file)) for file in REFERENCE_GPKG_HASHES.keys()
    }

    print("Generated CSV hashes: ", generated_csv_hashes)
    print("Generated GPKG hashes: ", generated_gpkg_hashes)

    for file in REFERENCE_CSV_HASHES.keys():
        assert REFERENCE_CSV_HASHES[file] == generated_csv_hashes[file]

    for file in REFERENCE_GPKG_HASHES.keys():
        assert REFERENCE_GPKG_HASHES[file] == generated_gpkg_hashes[file]

def test_determinism_matsim(tmpdir):
    data_path = str(tmpdir.mkdir("data"))
    testdata.create(data_path)

    for index in range(2):
        _test_determinism_matsim(index, data_path, tmpdir)

def _test_determinism_matsim(index, data_path, tmpdir):
    print("Running index %d" % index)

    cache_path = str(tmpdir.mkdir("cache_%d" % index))
    output_path = str(tmpdir.mkdir("output_%d" % index))
    config = dict(
        data_path = data_path, output_path = output_path,
        regions = [10, 11], sampling_rate = 1.0, hts = "entd",
        random_seed = 1000, processes = 1,
        secloc_maximum_iterations = 10,
        maven_skip_tests = True
    )

    stages = [
        dict(descriptor = "matsim.output"),
    ]

    synpp.run(stages, config, working_directory = cache_path)

    REFERENCE_HASHES = {
        #"ile_de_france_population.xml.gz":  "e1407f918cb92166ebf46ad769d8d085",
        #"ile_de_france_network.xml.gz":     "5f10ec295b49d2bb768451c812955794",
        "ile_de_france_households.xml.gz":  "cdbd6ed5b175328861f237dc58dee1ff",
        #"ile_de_france_facilities.xml.gz":  "5ad41afff9ae5c470082510b943e6778",
        "ile_de_france_config.xml":         "f374807f12a5151fe1efb6e9904e1a56"
    }

    # activities.gpkg, trips.gpkg, meta.json,
    # ile_de_france_transit_schedule.xml.gz, ile_de_france_transit_vehicles.xml.gz

    # TODO: Output of the Java part is not deterministic, probably because of
    # the ordering of persons / facilities. Fix that! Same is true for GPKG. A
    # detailed inspection of meta.json would make sense!

    generated_hashes = {
        file: hash_file("%s/%s" % (output_path, file)) for file in REFERENCE_HASHES.keys()
    }

    print("Generated hashes: ", generated_hashes)

    for file in REFERENCE_HASHES.keys():
        assert REFERENCE_HASHES[file] == generated_hashes[file]
