# 1. 存储方案

1. 使用redis做写服务

   ```
   user_id: {
      article_id: read_time 
   }
   
   ```

2. 定时同步到MySQL中

# 2. 存储流程

1. 在文章详情接口中保存到redis中

2. 每10分钟定时从redis中取数据保存到mysql中

3. 清除redis中的缓存记录

# 3. 读取流程

* 对于请求的第一页数据

    从redis中读取并清除用户的阅读记录

    然后从MySQL中读取
    
* 对于非第一页数据

    直接从MySQL中读取 