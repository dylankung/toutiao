```sql
alter table news_read add update_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间';
```