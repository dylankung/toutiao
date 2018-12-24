```http
curl -X PUT 172.17.0.135:9200/articles -H 'Content-Type: application/json' -d'
{
   "settings" : {
      "number_of_shards" : 3,
      "number_of_replicas" : 1
   }
}
'

```



```http

curl -X PUT 172.17.0.135:9200/articles/article/_mapping -H 'Content-Type: application/json' -d'
{
    "article": {
        "_all": {
            "analyzer": "ik_max_word",
            "search_analyzer": "ik_max_word",
            "term_vector": "no",
            "store": "false"
        },
        "properties": {
        	"article_id": {
                "type": "long",
                "store": "false"
        	},
        	"title": {
                "type": "text",
                "store": "false",
                "term_vector": "with_positions_offsets",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_max_word",
                "include_in_all": "true",
                "boost": 2
            },
            "content": {
                "type": "text",
                "store": "false",
                "term_vector": "with_positions_offsets",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_max_word",
                "include_in_all": "true"
            },
            "status": {
                "type": "byte",
                "store": "false",
                "include_in_all": "false"
            },
            "create_time": {
                "type": "date",
                "store": "false",
                "include_in_all": "false"
            }
        }
    }
}
'
```



