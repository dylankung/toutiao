```sql
alter table news_read add update_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间';


insert into news_article_statistic(article_id) select article_id from news_article_basic;
```