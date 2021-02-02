from tdms import url_site_location
from tdms import url_manpower
from tdms import url_attendence
from tdms import url_daily_work_sheet

urlpatterns = url_site_location.urlpatterns
urlpatterns += url_manpower.urlpatterns
urlpatterns += url_attendence.urlpatterns
urlpatterns += url_daily_work_sheet.urlpatterns
