import urllib.error
import urllib.request
from pathlib import Path

PROTOCOLS_DIR = Path(__file__).parent.parent / "data" / "protocols"

SOURCES = [
    {"file": "has_fausses_routes_2026.pdf", "year": 2026,
     "title": "HAS – Flash sécurité patient : fausses routes",
     "url": "https://has-sante.fr/upload/docs/application/pdf/2026-02/dir1/fsp_fausses_routes_-_lorsquune_petite_boulette_devient_un_tres_gros_pepin.pdf",
     "lang": "fr"},
    {"file": "has_chutes_synthese_2024.pdf", "year": 2024,
     "title": "HAS – Personnes âgées à risque de chute (synthèse)",
     "url": "https://www.has-sante.fr/upload/docs/application/pdf/2024-04/synthese_aps_personnes_agees_a_risque_de_chute.pdf",
     "lang": "fr"},
    {"file": "has_saed_2019.pdf", "year": 2019,
     "title": "HAS – Outil Saed : structurer la communication entre professionnels",
     "url": "https://www.has-sante.fr/upload/docs/application/pdf/2019-02/outil_14_outil__saed_.pdf",
     "lang": "fr"},
    {"file": "has_denutrition_fiche_2021.pdf", "year": 2021,
     "title": "HAS – Diagnostic de la dénutrition (fiche outil)",
     "url": "https://www.has-sante.fr/upload/docs/application/pdf/2022-05/reco368_fiche_outil_denutrition_pa_cd_20211110_v1.pdf",
     "lang": "fr"},
    {"file": "inrs_precautions_standard_2017.pdf", "year": 2017,
     "title": "INRS – Les précautions standard (synthèse des recommandations SF2H 2017)",
     "url": "https://www.inrs.fr/dam/inrs/CataloguePapier/DMT/TI-TM-42.pdf",
     "lang": "fr"},
    {"file": "has_transcription_prescriptions_2026.pdf", "year": 2026,
     "title": "HAS – Flash sécurité patient : (re)transcription des prescriptions",
     "url": "https://www.has-sante.fr/upload/docs/application/pdf/2026-02/dir1/flash_securite_patient__retranscription_des_prescriptions_medicamenteuses._copier_une_prescription_cest_risquer_de_coller_de.pdf",
     "lang": "fr"},
    {"file": "has_neuroleptiques_2022.pdf", "year": 2022,
     "title": "HAS – Flash sécurité patient : patient sous neuroleptique",
     "url": "https://has-sante.fr/upload/docs/application/pdf/2022-10/flash_securite_patient_-_patient_sous_neuroleptique_la_vigilance_est_la_bonne_pratique.pdf",
     "lang": "fr"},
    {"file": "has_violence_plan_prevention_2016.pdf", "year": 2016,
     "title": "HAS – Plan de prévention partagé (outil 03)",
     "url": "https://www.has-sante.fr/upload/docs/application/pdf/2016-10/outil_03_plan_prevention.pdf",
     "lang": "fr"},
    {"file": "has_isolement_synthese_2017.pdf", "year": 2017,
     "title": "HAS – Isolement en psychiatrie générale (synthèse)",
     "url": "https://www.has-sante.fr/upload/docs/application/pdf/2017-08/isolement_synthese_v3.pdf",
     "lang": "fr"},
    {"file": "has_contention_synthese_2017.pdf", "year": 2017,
     "title": "HAS – Contention mécanique en psychiatrie générale (synthèse)",
     "url": "https://has-sante.fr/upload/docs/application/pdf/2017-08/contention_synthese_v3_actualisee.pdf",
     "lang": "fr"}]

def download_all():
    import truststore
    truststore.inject_into_ssl()
    PROTOCOLS_DIR.mkdir(parents=True, exist_ok=True)
    for source in SOURCES:
        path = PROTOCOLS_DIR / source["file"]
        if path.exists():
            print("already here:", source["file"])
            continue
        print("downloading:", source["file"])
        try:
            urllib.request.urlretrieve(source["url"], path)
        except urllib.error.URLError as err:
            print("  FAILED:", source["file"], "->", err)
            continue
        if not path.read_bytes().startswith(b"%PDF"):
            path.unlink()
            print("  NOT A PDF (probably an HTML page):", source["file"], "-> download it by hand")

if __name__ == "__main__":
    download_all()