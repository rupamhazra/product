from sscrm.urls import (logistics_urls, marketing_urls, master_urls, sales_urls)


urlpatterns = logistics_urls.urlpatterns + marketing_urls.urlpatterns + master_urls.urlpatterns + sales_urls.urlpatterns
