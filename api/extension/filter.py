from rest_framework.filters import BaseFilterBackend


class SelfFilterBackend(BaseFilterBackend):
    """
    自定义过滤器
    """
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(user=request.user)
