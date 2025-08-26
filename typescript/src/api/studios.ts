import { components } from '../generated/types';

type StudioDetail = components['schemas']['StudioDetail'];
import { OtfHttpClient } from '../client/http-client';

/** Studio location and contact information */
export interface StudioLocation {
  phone_number?: string;
  latitude?: number;
  longitude?: number;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
}

/** Studio service offering with pricing */
export interface StudioService {
  service_uuid: string;
  name?: string;
  price?: string;
  qty?: number;
  online_price?: string;
  tax_rate?: string;
  current?: boolean;
  is_deleted?: boolean;
  created_date?: string;
  updated_date?: string;
}

/**
 * API for studio information and services
 * 
 * Provides access to studio details, favorite studios management,
 * geographical studio search, and studio service offerings.
 */
export class StudiosApi {
  private otfInstance: any; // Will be set after initialization
  
  /**
   * @param client - HTTP client for API requests
   * @param memberUuid - Authenticated member's UUID
   */
  constructor(private client: OtfHttpClient, private memberUuid: string) {}
  
  setOtfInstance(otf: any): void {
    this.otfInstance = otf;
  }

  /**
   * Gets detailed information for a specific studio
   * 
   * @param studioUuid - Studio UUID (defaults to member's home studio)
   * @returns Promise resolving to studio details
   */
  async getStudioDetail(studioUuid?: string): Promise<StudioDetail> {
    // Use home studio UUID if not provided
    const uuid = studioUuid || (this.otfInstance ? await this.otfInstance.homeStudioUuid : '');
    
    try {
      const response = await this.client.workoutRequest<any>({
        method: 'GET',
        apiType: 'default',
        path: `/mobile/v1/studios/${uuid}`,
      });

      return this.transformStudioData(response.data);
    } catch (error) {
      // Return empty model if not found (like Python implementation)
      return this.createEmptyStudioModel(uuid);
    }
  }

  /**
   * Gets the member's favorite studios
   * 
   * @returns Promise resolving to array of favorite studio details
   */
  async getFavoriteStudios(): Promise<StudioDetail[]> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'default',
      path: `/member/members/${this.memberUuid}/favorite-studios`,
    });

    const studioUuids = response.data.map((studio: any) => studio.studioUUId);
    
    // Get detailed info for each favorite studio
    const studioPromises = studioUuids.map((uuid: string) => this.getStudioDetail(uuid));
    return Promise.all(studioPromises);
  }

  /**
   * Adds studio(s) to member's favorites
   * 
   * @param studioUuids - Single studio UUID or array of UUIDs to add
   * @returns Promise resolving to updated favorite studios
   */
  async addFavoriteStudio(studioUuids: string | string[]): Promise<StudioDetail[]> {
    const uuids = Array.isArray(studioUuids) ? studioUuids : [studioUuids];
    
    if (uuids.length === 0) {
      throw new Error('studio_uuids is required');
    }

    const response = await this.client.workoutRequest<any>({
      method: 'POST',
      apiType: 'default',
      path: '/mobile/v1/members/favorite-studios',
      body: {
        studioUUIds: uuids,
      },
    });

    if (!response.data?.studios) {
      return [];
    }

    // Transform the returned studios
    return response.data.studios.map((studio: any) => this.transformStudioData(studio));
  }

  /**
   * Removes studio(s) from member's favorites
   * 
   * @param studioUuids - Single studio UUID or array of UUIDs to remove
   */
  async removeFavoriteStudio(studioUuids: string | string[]): Promise<void> {
    const uuids = Array.isArray(studioUuids) ? studioUuids : [studioUuids];
    
    if (uuids.length === 0) {
      throw new Error('studio_uuids is required');
    }

    await this.client.workoutRequest({
      method: 'DELETE',
      apiType: 'default',
      path: '/mobile/v1/members/favorite-studios',
      body: {
        studioUUIds: uuids,
      },
    });
  }

  /**
   * Gets services offered by a studio
   * 
   * @param studioUuid - Studio UUID (defaults to member's home studio)
   * @returns Promise resolving to array of studio services with pricing
   */
  async getStudioServices(studioUuid?: string): Promise<StudioService[]> {
    // Use home studio UUID if not provided  
    const uuid = studioUuid || (this.otfInstance ? await this.otfInstance.homeStudioUuid : '');
    
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'default',
      path: `/member/studios/${uuid}/services`,
    });

    // Transform services data and add studio reference
    return response.data.map((service: any) => ({
      service_uuid: service.serviceUUId,
      name: service.name,
      price: service.price,
      qty: service.qty,
      online_price: service.onlinePrice,
      tax_rate: service.taxRate,
      current: service.current,
      is_deleted: service.isDeleted,
      created_date: service.createdDate,
      updated_date: service.updatedDate,
    }));
  }

  /**
   * Searches for studios by geographical location
   * 
   * @param latitude - Latitude for search center (defaults to home studio location)
   * @param longitude - Longitude for search center (defaults to home studio location)
   * @param distance - Search radius in miles (max 250 miles, defaults to 50)
   * @returns Promise resolving to array of studios within specified distance
   */
  async searchStudiosByGeo(
    latitude?: number, 
    longitude?: number, 
    distance: number = 50
  ): Promise<StudioDetail[]> {
    // Use home studio coordinates if not provided
    if (!latitude || !longitude) {
      if (this.otfInstance) {
        const homeStudio = await this.otfInstance.homeStudio;
        latitude = latitude || homeStudio.location?.latitude;
        longitude = longitude || homeStudio.location?.longitude;
      }
    }

    const results = await this.getStudiosByGeoPaginated(latitude, longitude, distance);
    
    return results.map((studio: any) => this.transformStudioData(studio));
  }

  private async getStudiosByGeoPaginated(
    latitude?: number, 
    longitude?: number, 
    distance: number = 50
  ): Promise<any[]> {
    const maxDistance = Math.min(distance, 250); // max distance is 250 miles
    const pageSize = 100;
    let pageIndex = 1;
    const allResults: Record<string, any> = {};

    while (true) {
      const response = await this.client.workoutRequest<any>({
        method: 'GET',
        apiType: 'default',
        path: '/mobile/v1/studios',
        params: {
          latitude,
          longitude,
          distance: maxDistance,
          pageIndex,
          pageSize,
        },
      });

      const studios = response.data?.studios || [];
      const totalCount = response.data?.pagination?.totalCount || 0;

      // Add studios to results (keyed by UUID to avoid duplicates)
      studios.forEach((studio: any) => {
        allResults[studio.studioUUId] = studio;
      });

      if (Object.keys(allResults).length >= totalCount || studios.length === 0) {
        break;
      }

      pageIndex++;
    }

    return Object.values(allResults);
  }

  async getStudiosConcurrent(studioUuids: string[]): Promise<Record<string, StudioDetail>> {
    const promises = studioUuids.map(uuid => 
      this.getStudioDetail(uuid).then(data => ({ uuid, data }))
    );
    
    const results = await Promise.all(promises);
    return results.reduce((acc, { uuid, data }) => {
      acc[uuid] = data;
      return acc;
    }, {} as Record<string, StudioDetail>);
  }

  private transformStudioData(data: any): StudioDetail {
    // Transform API response to match exact generated StudioDetail type
    const transformedData: StudioDetail = {
      // Required fields exactly from generated type
      studio_uuid: data.studioUUId || '',
      contact_email: data.contactEmail || null,
      distance: data.distance || null,
      name: data.studioName || null,
      status: data.studioStatus || null,
      time_zone: data.timeZone || null,
      
      // Location - must match StudioLocation exactly
      location: data.studioLocation ? {
        address_line1: data.studioLocation.addressLine1 || data.studioLocation.address1 || null,
        address_line2: data.studioLocation.addressLine2 || data.studioLocation.address2 || null,
        city: data.studioLocation.city || null,
        postal_code: data.studioLocation.postalCode || null,
        state: data.studioLocation.state || data.studioLocation.territory || null,
        country: data.studioLocation.country || null,
        region: null,
        country_id: null,
        phone_number: data.studioLocation.phone || data.studioLocation.phoneNumber || null,
        latitude: data.studioLocation.latitude || null,
        longitude: data.studioLocation.longitude || null,
        physical_country_id: null,
        physical_region: null,
      } : undefined,
      
      // Payment options
      accepts_ach: data.acceptsAch || null,
      accepts_american_express: data.acceptsAmericanExpress || null,
      accepts_discover: data.acceptsDiscover || null,
      accepts_visa_master_card: data.acceptsVisaMasterCard || null,
      
      // Boolean flags
      allows_cr_waitlist: null,
      allows_dashboard_access: null,
      is_crm: null,
      is_integrated: data.isIntegrated || null,
      is_mobile: null,
      is_otbeat: null,
      is_web: null,
      
      // Other fields
      sms_package_enabled: null,
      studio_id: data.studioId || null,
      studio_number: data.studioNumber || null,
      studio_physical_location_id: data.studioPhysicalLocationId || null,
      studio_type_id: null,
      // studio_uuid_alt field not in generated type
      mbo_studio_id: data.mboStudioId || null,
      open_date: null,
      pricing_level: null,
      re_open_date: null,
      studio_token: null,
    };
    
    // Cast to any to bypass strict type checking for now
    // TODO: Update transformation to match exact generated type fields
    return transformedData as any;
  }

  private createEmptyStudioModel(studioUuid: string): StudioDetail {
    // Return empty model matching generated StudioDetail type exactly
    const emptyStudio: StudioDetail = {
      studio_uuid: studioUuid,
      contact_email: null,
      distance: null,
      location: undefined,
      name: null,
      status: null,
      time_zone: null,
      accepts_ach: null,
      accepts_american_express: null,
      accepts_discover: null,
      accepts_visa_master_card: null,
      allows_cr_waitlist: null,
      allows_dashboard_access: null,
      is_crm: null,
      is_integrated: null,
      is_mobile: null,
      is_otbeat: null,
      is_web: null,
      sms_package_enabled: null,
      studio_id: null,
      studio_number: null,
      studio_physical_location_id: null,
      studio_type_id: null,
      // studio_uuid_alt field not in generated type
      mbo_studio_id: null,
      open_date: null,
      pricing_level: null,
      re_open_date: null,
      studio_token: null,
    };
    
    return emptyStudio as any;
  }
}