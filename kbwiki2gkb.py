#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
# Convert KB format based on data from Wikipedia to General KB format
#
# author: Tomáš Volf
"""

import argparse
import os
import re
from collections import OrderedDict

INFILE_KB_HEAD = "HEAD-KB"  # name of KB HEAD file in Wikipedia KB format
INFILE_KB_DATA = "KBstatsMetrics.all"  # name of KB data file in Wikipedia KB format
INFILE_KB_HEAD_TYPE = "TYPE"  # name of column with TYPE in Wikipedia KB format

OUTFILE_KB_HEAD = "HEAD-KB.tsv"  # name of KB HEAD file in Generic KB format
OUTFILE_KB_DATA = "KB.tsv"  # name of KB data file in Generic KB format


# Basic type names of Generic KB format
COLTYPE_GENERIC = "__generic__"
COLTYPE_STATS = "__stats__"
COLTYPE_PERSON = "person"
COLTYPE_ARTIST = "artist"
COLTYPE_GROUP = "group"
COLTYPE_GEOGRAPHICAL = "geographical"
COLTYPE_ORGANISATION = "organisation"
COLTYPE_EVENT = "event"


# >>> Unique column codes of Generic KB format for processing conversion of formats
__GENERIC_ID = "__GENERIC:ID"
__GENERIC_TYPE = "__GENERIC:TYPE"
__GENERIC_NAME = "__GENERIC:NAME"
__GENERIC_DISAMB = "__GENERIC:DISAMBINAME"
__GENERIC_ALIASES = "__GENERIC:ALIASES"
__GENERIC_DESCRIPTION = "__GENERIC:DESCRIPTION"
__GENERIC_ROLES = "__GENERIC:ROLES"
__GENERIC_FICTIONAL = "__GENERIC:FICTIONAL"
__GENERIC_URL_WIKIPEDIA = "__GENERIC:WIKIPEDIA_URL"
__GENERIC_URL_WIKIDATA = "__GENERIC:WIKIDATA_URL"
__GENERIC_URL_DBPEDIA = "__GENERIC:DBPEDIA_URL"
__GENERIC_IMAGES = "__GENERIC:IMAGES"

PERSON_GENDER = "PERSON:GENDER"
PERSON_BDATE = "PERSON:BDATE"
PERSON_BPLACE = "PERSON:BPLACE"
PERSON_DDATE = "PERSON:DDATE"
PERSON_DPLACE = "PERSON:DPLACE"
PERSON_NATIONALITIES = "PERSON:NATIONALITIES"

GROUP_INDIVIDUALS = "GROUP:INDIVIDUALS"
GROUP_GENDERS = "GROUP:GENDERS"
GROUP_BDATES = "GROUP:BDATES"
GROUP_BPLACES = "GROUP:BPLACES"
GROUP_DDATES = "GROUP:DDATES"
GROUP_DPLACES = "GROUP:DPLACES"
GROUP_NATIONALITIES = "GROUP:NATIONALITIES"

ARTIST_FORMS = "ARTIST:FORMS"
ARTIST_INFLUENCERS = "ARTIST:INFLUENCERS"
ARTIST_INFLUENCEES = "ARTIST:INFLUENCEES"
ARTIST_ULANID = "ARTIST:ULAN_ID"
ARTIST_OTHER_URLS = "ARTIST:OTHER_URLS"

ORG_FOUNDED = "ORGANISATION:FOUNDED"
ORG_CANCELLED = "ORGANISATION:CANCELLED"
ORG_LOCATION = "ORGANISATION:LOCATION"
ORG_TYPE = "ORGANISATION:TYPE"

EVENT_START = "EVENT:START_DATE"
EVENT_END = "EVENT:END_DATE"
EVENT_LOCATIONS = "EVENT_LOCATIONS"
EVENT_TYPE = "EVENT:TYPE"

GEO_LAT = "GEO:LATITUDE"
GEO_LONG = "GEO:LONGITUDE"
GEO_TYPES = "GEO:TYPES"
GEO_COUNTRY = "GEO:COUNTRY"
GEO_POPULATION = "GEO:POPULATION"
GEO_ELEVATION = "GEO:ELEVATION"
GEO_AREA = "GEO:AREA"
GEO_TZONES = "GEO:TIMEZONES"
GEO_FCODE = "GEO:FEATURE_CODE"
GEO_GIDS = "GEO_GEONAMES_IDS"

__STATS_WBACKLINKS = "__STATS:WIKI_BACKLINKS"
__STATS_WHITS = "__STATS:WIKI_HITS"
__STATS_WPRIMSENSE = "__STATS:WIKI_PRIMARY_SENSE"
__STATS_WSCORE = "__STATS:WIKI_SCORE"
__STATS_SCORE_METRICS = "__STATS:SCORE_METRICS"
__STATS_CONFIDENCE = "__STATS:CONFIDENCE"
# <<< Unique column codes of Generic KB format for processing conversion of formats


# Map of conversion Wikipedia KB format types to main/basic types of Generic KB format
MAP_ENTITIES_BASETYPES = {
    # WikiKB types : GenericKB main/basic types
    "person": COLTYPE_PERSON,
    "person:fictional": COLTYPE_PERSON,
    "person:group": COLTYPE_GROUP,
    "person:artist": COLTYPE_ARTIST,
    "country": COLTYPE_GEOGRAPHICAL,
    "country:former": COLTYPE_GEOGRAPHICAL,
    "settlement": COLTYPE_GEOGRAPHICAL,
    "watercourse": COLTYPE_GEOGRAPHICAL,
    "waterarea": COLTYPE_GEOGRAPHICAL,
    "geo:relief": COLTYPE_GEOGRAPHICAL,
    "geo:waterfall": COLTYPE_GEOGRAPHICAL,
    "geo:island": COLTYPE_GEOGRAPHICAL,
    "geo:peninsula": COLTYPE_GEOGRAPHICAL,
    "geo:continent": COLTYPE_GEOGRAPHICAL,
    "organisation": COLTYPE_ORGANISATION,
    "event": COLTYPE_EVENT
}

# Map of main types of Generic KB format to set of consisting types (except generic types prefixed and suffixed with underscore, which are present always)
MAP_BASETYPES_COMPOSITE_TYPES = {
    COLTYPE_PERSON: [COLTYPE_PERSON],
    COLTYPE_GROUP: [COLTYPE_GROUP],
    COLTYPE_ARTIST: [COLTYPE_PERSON, COLTYPE_ARTIST],
    COLTYPE_GEOGRAPHICAL: [COLTYPE_GEOGRAPHICAL],
    COLTYPE_ORGANISATION: [COLTYPE_ORGANISATION],
    COLTYPE_EVENT: [COLTYPE_EVENT]
}


# >>> Column names (eventually with flags and other properties) of Generic KB format
HEAD_GENERIC = OrderedDict(
    [
        # (GenericKB column code , GenericKB column name (eventually with flags and other properties))
        (__GENERIC_ID, "ID"),
        (__GENERIC_TYPE, "TYPE"),
        (__GENERIC_NAME, "NAME"),
        (__GENERIC_DISAMB, "DISAMBIGUATION NAME"),
        (__GENERIC_ALIASES, "{m}ALIASES"),
        (__GENERIC_DESCRIPTION, "DESCRIPTION"),
        (__GENERIC_ROLES, "{m}ROLES"),
        (__GENERIC_FICTIONAL, "FICTIONAL"),
        (__GENERIC_URL_WIKIPEDIA, "{u}WIKIPEDIA URL"),
        (__GENERIC_URL_WIKIDATA, "{u}WIKIDATA URL"),
        (__GENERIC_URL_DBPEDIA, "{u}DBPEDIA URL"),
        (__GENERIC_IMAGES, "{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGES"),
    ]
)

HEAD_PERSON = OrderedDict(
    [
        # (GenericKB column code , GenericKB column name (eventually with flags and other properties))
        (PERSON_GENDER, "GENDER"),
        (PERSON_BDATE, "{e}DATE OF BIRTH"),
        (PERSON_BPLACE, "PLACE OF BIRTH"),
        (PERSON_DDATE, "{e}DATE OF DEATH"),
        (PERSON_DPLACE, "PLACE OF DEATH"),
        (PERSON_NATIONALITIES, "{m}NATIONALITIES"),
    ]
)

HEAD_GROUP = OrderedDict(
    [
        # (GenericKB column code , GenericKB column name (eventually with flags and other properties))
        (GROUP_INDIVIDUALS, "{m}INDIVIDUAL NAMES"),
        (GROUP_GENDERS, "{m}GENDERS"),
        (GROUP_BDATES, "{me}DATES OF BIRTH"),
        (GROUP_BPLACES, "{m}PLACES OF BIRTH"),
        (GROUP_DDATES, "{me}DATES OF DEATH"),
        (GROUP_DPLACES, "{m}PLACES OF DEATH"),
        (GROUP_NATIONALITIES, "{m}NATIONALITIES"),
    ]
)

HEAD_ARTIST = OrderedDict(
    [
        # (GenericKB column code , GenericKB column name (eventually with flags and other properties))
        (ARTIST_FORMS, "{m}ART FORMS"),
        (ARTIST_INFLUENCERS, "{m}INFLUENCERS"),
        (ARTIST_INFLUENCEES, "{m}INFLUENCEES"),
        (ARTIST_ULANID, "ULAN ID"),
        (ARTIST_OTHER_URLS, "{mu}OTHER URLS"),
    ]
)

HEAD_GEOGRAPHICAL = OrderedDict(
    [
        # (GenericKB column code , GenericKB column name (eventually with flags and other properties))
        (GEO_LAT, "LATITUDE"),
        (GEO_LONG, "LONGITUDE"),
        (GEO_TYPES, "{m}GEOTYPES"),
        (GEO_COUNTRY, "COUNTRY"),
        (GEO_POPULATION, "POPULATION"),
        (GEO_ELEVATION, "ELEVATION"),
        (GEO_AREA, "AREA"),
        (GEO_TZONES, "{m}TIMEZONES"),
        (GEO_FCODE, "FEATURE CODE"),
        (GEO_GIDS, "{m}GEONAMES IDS"),
    ]
)

HEAD_ORGANISATION = OrderedDict(
    [
        (ORG_FOUNDED, "FOUNDED"),
        (ORG_CANCELLED, "CANCELLED"),
        (ORG_LOCATION, "LOCATION"),
        (ORG_TYPE, "ORGANISATION_TYPE")
    ]
)

HEAD_EVENT = OrderedDict(
    [
        (EVENT_START, "START"),
        (EVENT_END, "END"),
        (EVENT_LOCATIONS, "LOCATION"),
        (EVENT_TYPE, "EVENT_TYPE")
    ]
)

HEAD_STATS = OrderedDict(
    [
        # (GenericKB column code , GenericKB column name (eventually with flags and other properties))
        (__STATS_WBACKLINKS, "WIKI BACKLINKS"),
        (__STATS_WHITS, "WIKI HITS"),
        (__STATS_WPRIMSENSE, "WIKI PRIMARY SENSE"),
        (__STATS_WSCORE, "SCORE WIKI"),
        (__STATS_SCORE_METRICS, "SCORE METRICS"),
        (__STATS_CONFIDENCE, "CONFIDENCE"),
    ]
)
# <<< Column names (eventually with flags and other properties) of Generic KB format


# Map of basic types to consisting column codes and names (all in GenericKB)
MAP_TYPES_COLUMNS = OrderedDict(
    [
        # (Basic GenericKB type , GenericKB columns codes and names)
        (COLTYPE_GENERIC, HEAD_GENERIC),
        (COLTYPE_PERSON, HEAD_PERSON),
        (COLTYPE_GROUP, HEAD_GROUP),
        (COLTYPE_ARTIST, HEAD_ARTIST),
        (COLTYPE_GEOGRAPHICAL, HEAD_GEOGRAPHICAL),
        (COLTYPE_ORGANISATION, HEAD_ORGANISATION),
        (COLTYPE_EVENT, HEAD_EVENT),
        (COLTYPE_STATS, HEAD_STATS),
    ]
)

# Map of GenericKB column code to WikipediaKB columns
MAP_NEWCOLS_OLDCOLS = {
    __GENERIC_ID: "ID",
    __GENERIC_TYPE: "TYPE",
    __GENERIC_NAME: "NAME",
    __GENERIC_DISAMB: "ORIGINAL_WIKINAME",
    __GENERIC_ALIASES: "ALIASES",
    __GENERIC_DESCRIPTION: "DESCRIPTION",
    # __GENERIC_ROLES: None,
    # __GENERIC_FICTIONAL: None,
    __GENERIC_URL_WIKIPEDIA: "WIKIPEDIA LINK",
    # __GENERIC_URL_WIKIDATA: None,
    # __GENERIC_URL_DBPEDIA: None,
    __GENERIC_IMAGES: "IMAGE",
    PERSON_GENDER: "GENDER",
    PERSON_BDATE: "DATE OF BIRTH",
    PERSON_BPLACE: "PLACE OF BIRTH",
    PERSON_DDATE: "DATE OF DEATH",
    PERSON_DPLACE: "PLACE OF DEATH",
    PERSON_NATIONALITIES: "NATIONALITY",
    # GROUP_INDIVIDUALS: None,
    GROUP_GENDERS: "GENDER",
    GROUP_BDATES: "DATE OF BIRTH",
    GROUP_BPLACES: "PLACE OF BIRTH",
    GROUP_DDATES: "DATE OF DEATH",
    GROUP_DPLACES: "PLACE OF DEATH",
    GROUP_NATIONALITIES: "NATIONALITIES",
    # ARTIST_FORMS: None,
    # ARTIST_INFLUENCERS: None,
    # ARTIST_INFLUENCEES: None,
    # ARTIST_ULANID: None,
    # ARTIST_OTHER_URLS: None,
    GEO_LAT: "LATITUDE",
    GEO_LONG: "LONGITUDE",
    # GEO_TYPES: None,
    GEO_COUNTRY: "COUNTRY",
    GEO_POPULATION: "POPULATION",
    # GEO_ELEVATION: None,
    GEO_AREA: "AREA",
    # GEO_TZONES: None,
    # GEO_FCODE: None,
    # GEO_GIDS: None,
    __STATS_WBACKLINKS: "WIKI BACKLINKS",
    __STATS_WHITS: "WIKI HITS",
    __STATS_WPRIMSENSE: "WIKI PRIMARY SENSE",
    __STATS_WSCORE: "SCORE WIKI",
    __STATS_SCORE_METRICS: "SCORE METRICS",
    __STATS_CONFIDENCE: "CONFIDENCE",
}


# Role column in GenericKB may be based on different columns of WikipediaKB depending on the type of entity - map GenericKB basic type to WikipediaKB column name
MAP_COLROLE_OLDCOL = {COLTYPE_PERSON: "JOBS"}


# Transform KB HEAD in WikipediaKB format to GenericKB format
def transform_head(fout_head):
    for ent_type, ent_columns in MAP_TYPES_COLUMNS.items():
        out_columns = []
        for ent_column in ent_columns.values():
            out_columns.append(ent_column)
        if len(out_columns):
            out_columns[0] = "<{}>{}".format(ent_type, out_columns[0])
        fout_head.write("\t".join(out_columns) + "\n")


# Transform KB data in WikipediaKB format to GenericKB format
def transform_data(in_head, in_kb, fout_kb):
    in_columns = dict()
    col_type = None
    # list of columns with their positional index for each entity type of WikipediaKB format
    with open(in_head, "r", encoding="utf8") as fin_head:
        for line in fin_head:
            line = line.strip("\n")
            ent_type = re.search(r"<(.*?)>", line)
            if ent_type:
                ent_type = ent_type.group(1)
                line = re.sub(r"<.*?>", "", line)
                line = re.sub(r"{.*?}", "", line)
                line = re.sub(r"\[.*?\]", "", line)
                in_columns[ent_type.lower()] = {
                    key: i for i, key in enumerate(line.split("\t"))
                }
                if not col_type:
                    col_type = in_columns[ent_type][INFILE_KB_HEAD_TYPE]
    # print(in_columns)
    with open(in_kb, "r", encoding="utf8") as fin_kb:
        for line in fin_kb:
            line = line.strip("\n")
            # line of data from KB in WikipediaKB format
            in_data = line.split("\t")
            # entity type of this line
            in_type = in_data[col_type].lower()
            out_basetype = MAP_ENTITIES_BASETYPES[in_type]
            out_types = MAP_BASETYPES_COMPOSITE_TYPES[out_basetype]
            out_alltypes = [COLTYPE_GENERIC] + out_types + [COLTYPE_STATS]
            out_data = []
            for out_type in out_alltypes:
                for out_column, trash in MAP_TYPES_COLUMNS[out_type].items():
                    # Type is consisting of multiple types (except generic types prefixed and suffixed by underscore) in GenericKB format
                    if out_column == __GENERIC_TYPE:
                        out_data.append("+".join(out_types))
                    # Fictional flag of GenericKB format is based on "person:fictional" entity type of WikipediaKB format
                    elif out_column == __GENERIC_FICTIONAL:
                        if in_type == "person:fictional":
                            out_data.append("1")
                        # If entity type is person (except group), it is likely to be a non-fictional entity
                        elif in_type.startswith("person") and in_type != "person:group":
                            out_data.append("0")
                        # ...otherwise we do not know
                        else:
                            out_data.append("")
                    # Special processing for column ROLES of GenericKB format
                    elif out_column == __GENERIC_ROLES:
                        if out_basetype in MAP_COLROLE_OLDCOL:
                            out_data.append(
                                in_data[
                                    in_columns[in_type][
                                        MAP_COLROLE_OLDCOL[out_basetype]
                                    ]
                                ]
                            )
                        else:
                            out_data.append("")
                    # Special processing for column GEOTYPES of GenericKB format
                    elif out_column == GEO_TYPES:
                        out_data.append(in_type.split(":")[-1])
                    # For column code of GenericKB format find data in KB of WikipediaKB format (with help of WikipediaKB HEAD definition and its entity types)
                    else:
                        if (
                            out_column in MAP_NEWCOLS_OLDCOLS
                            and in_type in in_columns
                            and MAP_NEWCOLS_OLDCOLS[out_column] in in_columns[in_type]
                        ):
                            out_data.append(
                                in_data[
                                    in_columns[in_type][MAP_NEWCOLS_OLDCOLS[out_column]]
                                ]
                            )
                        else:
                            out_data.append("")
            if in_type in in_columns:
                fout_kb.write("\t".join(out_data) + "\n")


parser = argparse.ArgumentParser(
    description="Convert KB in wikipedia format to generic KB format."
)
parser.add_argument(
    "--indir",
    default=".",
    help="Input files (wikipedia format) directory path (default: %(default)s).",
)
parser.add_argument(
    "--outdir",
    default=".",
    help="Output files (generic format) directory path (default: %(default)s).",
)
parser.add_argument(
    "--inhead",
    default=INFILE_KB_HEAD,
    help="Input KB head (wikipedia format) file name (default: %(default)s).",
)
parser.add_argument(
    "--inkb",
    default=INFILE_KB_DATA,
    help="Input KB data (wikipedia format) file name (default: %(default)s).",
)
parser.add_argument(
    "--outkb",
    default=OUTFILE_KB_DATA,
    help="Output KB (generic format) file name\n(default: %(default)s).",
)
args = parser.parse_args()

outkb = os.path.join(args.outdir, args.outkb)
with open(outkb, "w") as fout_kb:
    with open(os.path.join(args.indir, "VERSION"), "r") as fin_version:
        fout_kb.write("VERSION=" + fin_version.read())
    fout_kb.write("\n")
    transform_head(fout_kb)
    fout_kb.write("\n")
    transform_data(
        os.path.join(args.indir, args.inhead),
        os.path.join(args.indir, args.inkb),
        fout_kb,
    )
