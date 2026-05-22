from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin.models import LogEntry

from .models import CandidateCertification, CandidateProfile, CompanyProfile, JobApplication, JobOffer


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
    pending_companies = CompanyProfile.objects.filter(is_approved=False).select_related('user')
    extra_context.update({
        'user_count': User.objects.count(),
        'admin_count': User.objects.filter(is_staff=True).count(),
        'active_count': User.objects.filter(is_active=True).count(),
        'pending_count': pending_companies.count(),
        'pending_companies': list(pending_companies.order_by('-created_at')),
        'recent_users': list(User.objects.order_by('-date_joined')[:5]),
    })
    return original_index(request, extra_context)

admin.site.index = custom_index


class CandidateCertificationInline(admin.TabularInline):
    model = CandidateCertification
    extra = 0


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "phone_number", "city", "education_level", "is_public", "updated_at")
    search_fields = ("user__first_name", "user__last_name", "user__username", "skills", "city")
    list_filter = ("education_level", "is_public", "country")
    inlines = [CandidateCertificationInline]


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ("company_name", "industry", "company_size", "city", "country", "is_approved", "created_at")
    search_fields = ("company_name", "user__username", "user__email", "city", "industry")
    list_filter = ("is_approved", "industry", "company_size", "country")
    list_editable = ("is_approved",)
    actions = ["approve_companies", "reject_companies"]

    @admin.action(description="✅ Approve selected companies")
    def approve_companies(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} company(ies) approved.")

    @admin.action(description="❌ Reject selected companies")
    def reject_companies(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} company(ies) rejected.")


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ("title", "company_name", "city", "job_type", "contract_type", "experience_level", "is_active", "posted_at")
    search_fields = ("title", "company_name", "city", "summary")
    list_filter = ("job_type", "contract_type", "experience_level", "is_active", "is_remote")


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "job_offer", "status", "submitted_at")
    search_fields = ("full_name", "email", "job_offer__title", "job_offer__company_name")
    list_filter = ("status", "submitted_at")
