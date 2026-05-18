from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin.models import LogEntry


# Unregister default User admin to use custom one
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    pass


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag')
    list_filter = ('action_flag', 'content_type')
    search_fields = ('object_repr', 'user__username')
    ordering = ('-action_time',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.site_header = "Administration"
admin.site.site_title = "Administration"
admin.site.index_title = "Administration"


# Add dashboard context to admin index
original_index = admin.site.index

def custom_index(request, extra_context=None):
    if extra_context is None:
        extra_context = {}
    extra_context.update({
        'user_count': User.objects.count(),
        'admin_count': User.objects.filter(is_staff=True).count(),
        'active_count': User.objects.filter(is_active=True).count(),
        'activity_count': LogEntry.objects.count(),
        'recent_users': list(User.objects.order_by('-date_joined')[:5]),
    })
    return original_index(request, extra_context)

admin.site.index = custom_index