from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import EnumerationResult
from InformationGathering.models import Target
from .collector.enumerator import DeepWideEnumerator


@method_decorator(csrf_exempt, name='dispatch')
class StartEnumerationAPI(View):
    def post(self, request, target_id):
        try:
            target = Target.objects.get(id=target_id)
        except Target.DoesNotExist:
            return JsonResponse({"error": "Target not found"}, status=404)

        ip = target.host
        enumerator = DeepWideEnumerator(ip)
        results = enumerator.run_all()

        result = EnumerationResult.objects.create(
            target=target,
            smb_shares=results.get("smb_shares"),
            users_groups=results.get("users_groups"),
            services_banners=str(results.get("services_banners")),
            rpc_info=results.get("rpc_info"),
            netbios_info=results.get("netbios"),
            snmp_data=results.get("snmp"),
            ldap_data="\n".join(results.get("ldap")) if isinstance(results.get("ldap"), list) else results.get("ldap"),
            os_info=results.get("os_info_hostname"),
            hidden_web_content=results.get("hidden_web_content"),
            tools_used="smbclient,enum4linux,nmap,rpcclient,nmblookup,snmpwalk,ldap3,dirsearch",
            raw_output=None
        )

        return JsonResponse({"status": "success", "result_id": result.id})
