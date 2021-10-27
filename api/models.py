from django.db import models

class Source(models.Model):
    genome = models.CharField(max_length=255)
    assembly = models.CharField(max_length=255)
    track = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'source'
        
class Feature(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'feature'

class Chr(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'chr'
        
        
class Entity(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    gene_id = models.IntegerField()
    transcript_id = models.IntegerField()
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    chr = models.ForeignKey(Chr, on_delete=models.CASCADE)
    start = models.IntegerField()
    end = models.IntegerField()
    strand = models.CharField(max_length=1)
    name = models.CharField(max_length=255)
    entity_id = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'entity'
        

        
class Bin(models.Model):
    chr = models.ForeignKey(Chr, on_delete=models.CASCADE)
    start = models.IntegerField()
    width = models.IntegerField()
    entities = models.ManyToManyField(Entity)
    
    class Meta:
        db_table = 'bin'
        
#class BinEntities(models.Model):
#    bin = models.ForeignKey(Bin, on_delete=models.CASCADE)
#    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
#
#    class Meta:
#        db_table = 'bin_entities'