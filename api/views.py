from django.http import JsonResponse
from django.core.cache import cache
from django.db.models import Q

from genes import settings
from api.models import Source, Chr, Bin, Entity
from api.serializers import SourceSerializer

import libhttp
import libhttpdna

ABOUT_JSON = JsonResponse({'name':'genes','version':'3.0','copyright':'Copyright (C) 2018-2020 Antony Holmes'}, safe=False)
EMPTY_JSON = JsonResponse([], safe=False)

def _gene_to_json(gene):
    return {'loc':gene.loc, 'strand':gene.strand, 'type':gene.level, 'ids':gene.properties, 'tags':gene.tags}

def _genes_to_json(genes):
    ret = []
    
    for gene in genes:
        json = _gene_to_json(gene)
        
#        if gene.level == 1:
#            json['transcripts'] = _genes_to_json(gene.children(libgenomic.TRANSCRIPT))
#        elif gene.level == 2:
#            json['exons'] = _genes_to_json(gene.children(libgenomic.EXON))
#        else:
#            pass
        
        ret.append(json)
    
    return ret

def about(request):
    return ABOUT_JSON

def _get_chr(loc):
    chrs = Chr.objects.filter(name=loc.chr)
    
    if len(chrs) > 0:
        return chrs[0]
    else:
        return None

def _get_source(genome, assembly, track):
    sources = Source.objects.filter(genome__iexact=genome, assembly__iexact=assembly, track__iexact=track)
    
    if len(sources) > 0:
        return sources[0]
    else:
        return None
    
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
        .add('w', default_value=16384) \
        .parse(request)
    
    
    genome = id_map['genome'].lower()
    assembly = id_map['assembly'].lower()
    track = id_map['track'].lower()
    s = id_map['s']
    e = id_map['e']
    w = id_map['w']
    
    # try to stop users specifying wrong genome
    if 'mm' in assembly:
        genome = 'mouse'
        
    cache_key = ':'.join(['gene_search', genome, assembly, track, str(s), str(e)])
        
    data = cache.get(cache_key)
    
    # shortcut and return cached copy
    #if data is not None:
     #   return data
    
    loc = libhttpdna.get_loc_from_params(id_map)
    
    if loc is None:
        return JsonResponse({'success': False, 'error': 'Invalid location'}, safe=False)

    source = _get_source(genome, assembly, track)
    
    if source is None:
        return JsonResponse({'success': False, 'error': 'Invalid source'}, safe=False)

    chr = _get_chr(loc)
    
    if chr is None:
        return JsonResponse({'success': False, 'error': 'Invalid chr'}, safe=False)
    
    bins = Bin.objects.filter(chr=chr, 
                              start__gte=s, 
                              start__lt=e, 
                              width=w, 
                              entities__source=source).order_by('start')
    
    if len(bins) == 0:
        return EMPTY_JSON
    
    used = set()
    features = []
    
    for bin in bins:
        entities = bin.entities.order_by('id')
        
        for entity in entities:
            if entity.id in used:
                continue
            
            #if entity.end < s or entity.start > e:
            #    continue
            
            strand = entity.strand
            feature = entity.feature.name
            location = '{}:{}-{}'.format(chr.name, entity.start, entity.end)
            
            e = {'location':location, 'strand':strand}
            
            if entity.name != '':
                e['name'] = entity.name
            
            if feature == 'gene':
                gene = e
                gene['gene_id'] = entity.entity_id
                gene['transcripts'] = []
                features.append(gene)
            elif feature == 'transcript':
                transcript = e
                transcript['transcript_id'] = entity.entity_id
                transcript['exons'] = []
                gene['transcripts'].append(transcript)
            elif feature == 'exon':
                exon = e
                exon['exon_id'] = entity.entity_id
                transcript['exons'].append(exon)
            
            used.add(entity.id)
    
    data = JsonResponse({'location':loc.__str__(), 'genes':features}, safe=False)
    
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
        .parse(request)
    
    genome = id_map['genome'].lower()
    assembly = id_map['assembly'].lower()
    track = id_map['track'].lower()
    search = id_map['s']
       
    cache_key = ':'.join(['gene_search', genome, assembly, track, search])
        
    data = cache.get(cache_key)
    
    # shortcut and return cached copy
    #if data is not None:
    #    return data

    source = _get_source(genome, assembly, track)
    
    if source is None:
        return JsonResponse({'success': False, 'error': 'Invalid source'}, safe=False)

    entities = Entity.objects.filter(Q(source=source), Q(name__icontains=search) | Q(entity_id__icontains=search)).order_by('name')
    
    gene_ids = set()
    
    for entity in entities:
        gene_ids.add(entity.gene_id)
    
    features = []
    
    print(gene_ids)
    
    for id in sorted(gene_ids):
        entities = Entity.objects.filter(gene_id=id)
        
        for entity in entities:
            strand = entity.strand
            feature = entity.feature.name
            location = '{}:{}-{}'.format(entity.chr.name, entity.start, entity.end)
            
            e = {'location':location, 'strand':strand}
            
            if entity.name != '':
                e['name'] = entity.name
            
            if feature == 'gene':
                gene = e
                gene['gene_id'] = entity.entity_id
                gene['transcripts'] = []
                features.append(gene)
            elif feature == 'transcript':
                transcript = e
                transcript['transcript_id'] = entity.entity_id
                transcript['exons'] = []
                gene['transcripts'].append(transcript)
            elif feature == 'exon':
                exon = e
                exon['exon_id'] = entity.entity_id
                transcript['exons'].append(exon)
    
    data = JsonResponse(features, safe=False)
    
    cache.set(cache_key, data, settings.CACHE_TIME_S)
        
    return data


def databases(request):
    """
    List available databases.
    """
    
    data = cache.get('databases') # returns None if no key-value pair
    
    # shortcut and return cached copy
    #if data is not None:
    #    return data
    
    serializer = SourceSerializer(Source.objects.all(), many=True, read_only=True)
    resp = JsonResponse(serializer.data, safe=False)
    
    cache.set('databases', resp, settings.CACHE_TIME_S)
        
    return resp
    
    
