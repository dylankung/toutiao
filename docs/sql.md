```sql
alter table news_read add update_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间';


insert into news_article_statistic(article_id) select article_id from news_article_basic;


alter table news_channel add `sequence` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '序号';
alter table news_channel add `is_visible` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否可见';

alter table news_user_channel add `sequence` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '序号';

```