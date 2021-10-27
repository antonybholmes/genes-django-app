from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.core.cache import cache
import os
import sqlite3
import json

from genes import settings

import sys
import libhttp
import libhttpdna
import libgfb
import libgenomic


def _find(genome, assembly, track, chr, start, end):
    #print(genome, assembly, track)

    conn = sqlite3.connect(os.path.join(settings.DATA_DIR, 'genes.sqlite3'))

    q = "SELECT id FROM tracks WHERE genome=? AND assembly=? AND track=?"
    c = conn.execute(q, [genome.lower(), assembly, track])
    row = c.fetchone()
    track = row[0]

    loc = '{}:{}-{}'.format(chr, start, end)

    ret = {'loc': loc, 'genes': []}

    q = "SELECT id, chr, start, end, strand, ids FROM transcripts WHERE track_id=? AND chr=? AND ((start<=? AND end>?) OR (start<=? AND end>?) OR (start>? AND end<?)) ORDER BY start"
    c = conn.execute(q, [track, chr, start, start, end, end, start, end])
    transcripts = c.fetchall()

    for transcript in transcripts:
        transcript_id = transcript[0]
        s = transcript[2]
        e = transcript[3]
        loc = '{}:{}-{}'.format(chr, s, e)
        strand = transcript[4]
        ids = json.loads(transcript[5])

        t = {'loc': loc, 'strand': strand, 'type': 'transcript',
             'ids': ids, 'exons': [], 'tags': []}

        q = "SELECT id, exon_id, start, end FROM exons WHERE transcript_id=? ORDER BY start"
        c = conn.execute(q, [transcript_id])
        exons = c.fetchall()

        for exon in exons:
            s = exon[2]
            e = exon[3]
            loc = '{}:{}-{}'.format(chr, s, e)

            ex = {'loc': loc, 'strand': strand,
                  'type': 'exon', 'ids': ids, 'tags': []}
            t['exons'].append(ex)
        # break

        ret['genes'].append(t)

    conn.close()

    return ret  # json.dumps(ret)


def _search(genome, assembly, track, search):
    #print(genome, assembly, track)

    conn = sqlite3.connect(os.path.join(settings.DATA_DIR, 'genes.sqlite3'))

    q = "SELECT id FROM tracks WHERE genome=? AND assembly=? AND track=?"
    c = conn.execute(q, [genome.lower(), assembly, track])
    row = c.fetchone()
    track = row[0]

    ret = []

    q = "SELECT id, chr, start, end, strand, ids FROM transcripts WHERE track_id=? AND ids LIKE ? LIMIT 10"
    c = conn.execute(q, [track, '%{}%'.format(search)])
    transcripts = c.fetchall()

    for transcript in transcripts:
        transcript_id = transcript[0]
        chr = transcript[1]
        s = transcript[2]
        e = transcript[3]
        loc = '{}:{}-{}'.format(chr, s, e)
        strand = transcript[4]
        ids = json.loads(transcript[5])

        t = {'loc': loc, 'strand': strand, 'type': 'transcript',
             'ids': ids, 'exons': [], 'tags': []}

        q = "SELECT id, exon_id, start, end FROM exons WHERE transcript_id=? ORDER BY start"
        c = conn.execute(q, [transcript_id])
        exons = c.fetchall()

        for exon in exons:
            s = exon[2]
            e = exon[3]
            loc = '{}:{}-{}'.format(chr, s, e)

            ex = {'loc': loc, 'strand': strand,
                  'type': 'exon', 'ids': ids, 'tags': []}
            t['exons'].append(ex)
        # break

        ret.append(t)

    conn.close()

    return ret  # json.dumps(ret)


def _databases():
    conn = sqlite3.connect(os.path.join(settings.DATA_DIR, 'genes.sqlite3'))

    q = "SELECT id, genome, assembly, track FROM tracks ORDER BY genome, assembly, track"
    c = conn.execute(q)
    dbs = c.fetchall()

    ret = [{'genome': db[1], 'assembly': db[2], 'track': db[3]} for db in dbs]

    conn.close()

    return ret  # json.dumps(ret)



def _gene_to_json(gene):
    return {'loc': gene.loc, 'strand': gene.strand, 'type': gene.level, 'ids': gene.properties, 'tags': gene.tags}


def _genes_to_json(genes):
    ret = []

    for gene in genes:
        json = _gene_to_json(gene)

        if gene.level == libgenomic.GENE:
            json['transcripts'] = _genes_to_json(
                gene.children(libgenomic.TRANSCRIPT))
        elif gene.level == libgenomic.TRANSCRIPT:
            json['exons'] = _genes_to_json(gene.children(libgenomic.EXON))
        else:
            pass

        ret.append(json)

    return ret


def about(request):
    return JsonResponse({'name': 'genes', 'version': '2.0', 'copyright': 'Copyright (C) 2018-2019 Antony Holmes'}, safe=False)


def find(request):
    """
    Allow users to search for genes by location
    """

    # Defaults should find BCL6
    #id_map = libhttp.parse_params(request, {'genome':'Human', 'track':'gencode', 'assembly':'grch38', 'chr':'chr3', 's':187721377, 'e':187736497, 't':'g'})

    id_map = libhttp.ArgParser() \
        .add('genome', default_value='Human') \
        .add('track', default_value='gencode') \
        .add('assembly', default_value='grch38') \
        .add('chr', default_value='chr3') \
        .add('s', default_value=187721377) \
        .add('e', default_value=187736497) \
        .parse(request)

    genome = id_map['genome'].lower()
    assembly = id_map['assembly'].lower()
    track = id_map['track'].lower()
    chr = id_map['chr']
    s = id_map['s']
    e = id_map['e']

    # try to stop users specifying wrong genome
    if 'mm' in assembly:
        genome = 'mouse'

    cache_key = '_'.join(
        ['gene_search', genome, assembly, track, str(s), str(e)])

    data = cache.get(cache_key)

    # shortcut and return cached copy
    if data is not None:
        #print('Using gene search cache of', cache_key)
        return data

    loc = libhttpdna.get_loc_from_params(id_map)

    if loc is None:
        return JsonResponse({}, safe=False)

    #dir = os.path.join(settings.DATA_DIR, genome, assembly, track)

    #reader = libgfb.GFBReader(track, assembly, dir)

    #genes = reader.find_genes(loc)

    #gl = _genes_to_json(genes)

    #data = JsonResponse({'loc':loc.__str__(), 'genes':gl}, safe=False)

    ret = _find(genome, assembly, track, chr, s, e)

    data = JsonResponse(ret, safe=False)

    cache.set(cache_key, data, settings.CACHE_TIME_S)

    return data


def search(request):
    """
    Search for genes by name.
    """

    #id_map = libhttp.parse_params(request, {'genome':'Human', 'track':'gencode', 'assembly':'grch38', 's':'BCL6', 't':'g'})

    id_map = libhttp.ArgParser() \
        .add('genome', default_value='Human') \
        .add('track', default_value='gencode') \
        .add('assembly', default_value='grch38') \
        .add('chr', default_value='chr3') \
        .add('s', default_value='BCL6') \
        .add('e', default_value=187736497) \
        .parse(request)

    genome = id_map['genome'].lower()
    assembly = id_map['assembly'].lower()
    track = id_map['track'].lower()
    search = id_map['s']

    if 'mm' in assembly:
        genome = 'mouse'

    cache_key = '_'.join(['gene_search', genome, assembly, track, search])

    data = cache.get(cache_key)

    # shortcut and return cached copy
    if data is not None:
        #print('Using gene search cache of', cache_key)
        return data

    #dir = os.path.join(settings.DATA_DIR, genome, assembly, track)
    #reader = libgfb.GFBReader(track, assembly, dir)
    #genes = reader.get_genes(search)
    #gl = _genes_to_json(genes)
    #data = JsonResponse(gl, safe=False)

    ret = _search(genome, assembly, track, search)
    data = JsonResponse(ret, safe=False)

    cache.set(cache_key, data, settings.CACHE_TIME_S)

    return data


def databases(request):
    """
    List available databases.
    """

    data = cache.get('databases')  # returns None if no key-value pair

    # shortcut and return cached copy
    if data is not None:
        #print('Using vfs cache of', cache_key)
        return data

    files = os.listdir(settings.DATA_DIR)

    #ret = []

    #for file in files:
    #    d = os.path.join(settings.DATA_DIR, file)

    #    if os.path.isdir(d):
    #        genome = file

    #        files2 = os.listdir(d)

    #        for file2 in files2:
    #            d2 = os.path.join(d, file2)

    #            if os.path.isdir(d2):
    #                assembly = file2

    #                files3 = os.listdir(d2)

    #                for file3 in files3:
    #                    d3 = os.path.join(d2, file3)

    #                    if os.path.isdir(d3):
    #                        track = file3

    #                        ret.append({'genome': genome.capitalize(),
    #                                   'assembly': assembly, 'track': track})

    #data = JsonResponse(ret, safe=False)

    ret = _databases()
    data = JsonResponse(ret, safe=False)


    cache.set('databases', data, settings.CACHE_TIME_S)

    return data
