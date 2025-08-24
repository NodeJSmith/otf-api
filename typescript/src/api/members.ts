import { Member, MemberDetail } from 'otf-api-models';
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

    // Transform camelCase API response to snake_case model fields to match Python implementation
    const data = response.data;
    const transformedData = {
      member_uuid: data.memberUUId,
      first_name: data.firstName,
      last_name: data.lastName,
      email: data.email,
      phone_number: data.phoneNumber,
      date_of_birth: data.birthDay,
      gender: data.gender,
      locale: data.locale,
      weight: data.weight,
      weight_units: data.weightMeasure,
      height: data.height,
      height_units: data.heightMeasure,
      studio_display_name: data.userName,
      
      // Nested objects
      home_studio: {
        studio_uuid: data.homeStudio.studioUUId,
        studio_name: data.homeStudio.studioName,
        studio_number: data.homeStudio.studioNumber,
        time_zone: data.homeStudio.timeZone,
        studio_id: data.homeStudio.studioId,
        mbo_studio_id: data.homeStudio.mboStudioId,
        is_integrated: data.homeStudio.isIntegrated,
        studio_status: data.homeStudio.studioStatus,
      },
      
      profile: data.memberProfile ? {
        unit_of_measure: data.memberProfile.unitOfMeasure,
        max_hr_type: data.memberProfile.maxHrType,
        manual_max_hr: data.memberProfile.manualMaxHr,
        formula_max_hr: data.memberProfile.formulaMaxHr,
        automated_hr: data.memberProfile.automatedHr,
      } : null,
      
      class_summary: data.memberClassSummary ? {
        total_classes_booked: data.memberClassSummary.totalClassesBooked,
        total_classes_attended: data.memberClassSummary.totalClassesAttended,
        total_intro_classes: data.memberClassSummary.totalIntro,
        total_ot_live_classes_booked: data.memberClassSummary.totalOTLiveClassesBooked,
        total_ot_live_classes_attended: data.memberClassSummary.totalOTLiveClassesAttended,
        total_classes_used_hrm: data.memberClassSummary.totalClassesUsedHRM,
        total_studios_visited: data.memberClassSummary.totalStudiosVisited,
        first_visit_date: data.memberClassSummary.firstVisitDate,
        last_class_visited_date: data.memberClassSummary.lastClassVisitedDate,
        last_class_booked_date: data.memberClassSummary.lastClassBookedDate,
      } : null,
      
      addresses: data.addresses ? data.addresses.map((addr: any) => ({
        type: addr.type,
        address_line1: addr.address1,
        address_line2: addr.address2,
        city: addr.suburb,
        state: addr.territory,
        postal_code: addr.postalCode,
        country: addr.country,
      })) : [],
    };
    
    return transformedData as MemberDetail;
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