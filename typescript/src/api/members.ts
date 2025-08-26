import { components } from '../generated/types';

type MemberDetail = components['schemas']['MemberDetail'];
import { OtfHttpClient } from '../client/http-client';
import { API_ENDPOINTS } from '../types/config';

/**
 * API for member profile and membership operations
 * 
 * Provides access to member details, membership information, and profile data.
 */
export class MembersApi {
  /**
   * @param client - HTTP client for API requests
   * @param memberUuid - Authenticated member's UUID
   */
  constructor(private client: OtfHttpClient, private memberUuid: string) {}

  /**
   * Gets detailed member profile information
   * 
   * @returns Promise resolving to member details including home studio and membership info
   */
  async getMemberDetail(): Promise<MemberDetail> {
    const response = await this.client.request<any>({
      method: 'GET',
      baseUrl: API_ENDPOINTS.main,
      path: `/member/members/${this.memberUuid}`,
      params: { 
        include: 'memberAddresses,memberClassSummary' 
      },
    });

    // Transform camelCase API response to match exact Python model structure
    const data = response.data;
    const transformedData: MemberDetail = {
      // Required fields
      member_uuid: data.memberUUId,
      cognito_id: data.cognitoId || '',
      
      // Home studio - must match StudioDetail exactly (required)
      home_studio: {
        studio_uuid: data.homeStudio?.studioUUId || '',
        contact_email: data.homeStudio?.contactEmail || null,
        distance: null, // Not available from member detail API
        location: data.homeStudio?.studioLocation ? {
          address_line1: data.homeStudio.studioLocation.addressLine1 || null,
          address_line2: data.homeStudio.studioLocation.addressLine2 || null,
          city: data.homeStudio.studioLocation.city || null,
          postal_code: data.homeStudio.studioLocation.postalCode || null,
          state: data.homeStudio.studioLocation.state || null,
          country: data.homeStudio.studioLocation.country || null,
          region: null,
          country_id: null,
          phone_number: data.homeStudio.studioLocation.phone || null,
          latitude: data.homeStudio.studioLocation.latitude || null,
          longitude: data.homeStudio.studioLocation.longitude || null,
          physical_country_id: null,
          physical_region: null,
        } : undefined,
        name: data.homeStudio?.studioName || null,
        status: data.homeStudio?.studioStatus || null,
        time_zone: data.homeStudio?.timeZone || null,
        accepts_ach: null,
        accepts_american_express: null,
        accepts_discover: null,
        accepts_visa_master_card: null,
        allows_cr_waitlist: null,
        allows_dashboard_access: null,
        is_crm: null,
        is_integrated: data.homeStudio?.isIntegrated || null,
        is_mobile: null,
        is_otbeat: null,
        is_web: null,
        sms_package_enabled: null,
        studio_id: data.homeStudio?.studioId || null,
        mbo_studio_id: data.homeStudio?.mboStudioId || null,
        open_date: null,
        pricing_level: null,
        re_open_date: null,
        studio_number: data.homeStudio?.studioNumber || null,
        studio_physical_location_id: null,
        studio_token: null,
        studio_type_id: null,
      },
      
      // Profile - must match MemberProfile exactly (required)
      profile: {
        unit_of_measure: data.memberProfile?.unitOfMeasure || null,
        max_hr_type: data.memberProfile?.maxHrType || null,
        manual_max_hr: data.memberProfile?.manualMaxHr || null,
        formula_max_hr: data.memberProfile?.formulaMaxHr || null,
        automated_hr: data.memberProfile?.automatedHr || null,
        member_profile_uuid: null,
        member_optin_flow_type_id: null,
      },
      
      // All other required fields with default values
      created_by: null,
      created_date: null,
      home_studio_id: null,
      member_id: data.memberId || null,
      otf_acs_id: null,
      updated_by: null,
      updated_date: null,
      
      // Optional fields
      class_summary: data.memberClassSummary ? {
        total_classes_booked: data.memberClassSummary.totalClassesBooked || null,
        total_classes_attended: data.memberClassSummary.totalClassesAttended || null,
        total_intro_classes: data.memberClassSummary.totalIntro || null,
        total_ot_live_classes_booked: data.memberClassSummary.totalOTLiveClassesBooked || null,
        total_ot_live_classes_attended: data.memberClassSummary.totalOTLiveClassesAttended || null,
        total_classes_used_hrm: data.memberClassSummary.totalClassesUsedHRM || null,
        total_studios_visited: data.memberClassSummary.totalStudiosVisited || null,
        first_visit_date: data.memberClassSummary.firstVisitDate || null,
        last_class_visited_date: data.memberClassSummary.lastClassVisitedDate || null,
        last_class_booked_date: data.memberClassSummary.lastClassBookedDate || null,
        last_class_studio_visited: null,
      } : null,
      
      // Addresses - must match Address[] exactly
      addresses: data.addresses ? data.addresses.map((addr: any) => ({
        type: addr.type || null,
        address_line1: addr.address1 || null,
        address_line2: addr.address2 || null,
        city: addr.suburb || null,
        state_province_region: addr.territory || null,
        postal_code: addr.postalCode || null,
        country: addr.country || null,
        latitude: null,
        longitude: null,
        phone_number: null,
        tax_rate: null,
        introduction_message: null,
        physical_location_id: null,
        physical_country_id: null,
        member_address_uuid: null,
      })) : null,
      
      // Personal details
      studio_display_name: data.userName || null,
      first_name: data.firstName || null,
      last_name: data.lastName || null,
      email: data.email || null,
      phone_number: data.phoneNumber || null,
      birth_day: data.birthDay || null,
      gender: data.gender || null,
      locale: data.locale || null,
      weight: data.weight || null,
      weight_units: data.weightMeasure || null,
      height: data.height || null,
      height_units: data.heightMeasure || null,
      
      // Address fields
      address_line1: null,
      address_line2: null,
      city: null,
      state: null,
      postal_code: null,
      
      // MindBody fields
      mbo_id: data.mboId || null,
      mbo_status: data.mboStatus || null,
      mbo_studio_id: data.mboStudioId || null,
      mbo_unique_id: data.mboUniqueId || null,
      
      // Additional optional fields
      alternate_emails: null,
      cc_last4: null,
      cc_type: null,
      home_phone: null,
      intro_neccessary: null,
      is_deleted: null,
      is_member_verified: null,
      lead_prospect: null,
      max_hr: null,
      online_signup: null,
      phone_type: null,
      work_phone: null,
      year_imported: null,
    };
    
    return transformedData;
  }

  async updateMemberName(firstName: string, lastName: string): Promise<MemberDetail> {
    return this.client.request<MemberDetail>({
      method: 'PUT',
      baseUrl: API_ENDPOINTS.main,
      path: `/member/members/${this.memberUuid}`,
      body: {
        firstName: firstName,
        lastName: lastName,
      },
    });
  }

  async getMembership(): Promise<any> {
    return this.client.request({
      method: 'GET',
      baseUrl: API_ENDPOINTS.main,
      path: `/member/members/${this.memberUuid}/memberships`,
    });
  }

  async getPurchases(): Promise<any> {
    return this.client.request({
      method: 'GET',
      baseUrl: API_ENDPOINTS.main,
      path: `/member/members/${this.memberUuid}/purchases`,
    });
  }

  async getSmsNotificationSettings(): Promise<any> {
    return this.client.request({
      method: 'GET',
      baseUrl: API_ENDPOINTS.main,
      path: '/sms/v1/preferences',
    });
  }

  async updateSmsNotificationSettings(settings: any): Promise<any> {
    return this.client.request({
      method: 'POST',
      baseUrl: API_ENDPOINTS.main,
      path: '/sms/v1/preferences',
      body: settings,
    });
  }

  async getEmailNotificationSettings(): Promise<any> {
    return this.client.request({
      method: 'GET',
      baseUrl: API_ENDPOINTS.main,
      path: '/otfmailing/v2/preferences',
    });
  }

  async updateEmailNotificationSettings(settings: any): Promise<any> {
    return this.client.request({
      method: 'POST',
      baseUrl: API_ENDPOINTS.main,
      path: '/otfmailing/v2/preferences',
      body: settings,
    });
  }

  async getAppConfiguration(): Promise<any> {
    return this.client.request({
      method: 'GET',
      baseUrl: API_ENDPOINTS.main,
      path: '/member/app-configurations',
      requiresSigV4: true,
    });
  }
}