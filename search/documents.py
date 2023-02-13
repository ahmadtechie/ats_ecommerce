from elasticsearch_dsl import Document
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Completion

from category.models import Category
from store.models import Product


# ElasticSearch "model" mapping out what fields to index
@registry.register_document
class CategoryDocument(Document):
    category_name = fields.TextField(
        attr='category_name',
        fields={
            'suggest': fields.Completion(),
        }
    )

    class Index:
        name = "categories"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }

    class Django:
        model = Category
        name_suggest = Completion()
        fields = [
            'id', 'description', 'slug', 'category_img'
        ]


@registry.register_document
class ProductDocument(Document):
    product_name = fields.TextField(
        attr='product_name',
        fields={
            'suggest': fields.Completion(),
        }
    )

    category = fields.ObjectField(properties={
        'category_name': fields.TextField(),
        'slug': fields.TextField(),
        'description': fields.TextField(),
    })

    class Index:
        name = "products"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }

    class Django:
        model = Product
        fields = [
            'id', 'description', 'price', 'slug', 'image'
        ]
        related_models = [Category]

    def get_queryset(self):
        return super(ProductDocument, self).get_queryset().select_related(
            'category'
        )


# bulk indexing function
def bulk_indexing():
    ProductDocument.init()
    es = Elasticsearch()
    bulk(client=es, actions=(p.indexing() for p in Product.objects.all().iterator()))
