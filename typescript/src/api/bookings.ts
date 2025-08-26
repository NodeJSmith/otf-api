import { components } from '../generated/types';

type BookingV2 = components['schemas']['BookingV2'];
import { OtfHttpClient } from '../client/http-client';

/**
 * API for class booking and cancellation operations
 * 
 * Provides access to booking details and workout class management.
 */
export class BookingsApi {
  /**
   * @param client - HTTP client for API requests
   * @param memberUuid - Authenticated member's UUID
   */
  constructor(private client: OtfHttpClient, private memberUuid: string) {}

  /**
   * Gets detailed booking information
   * 
   * @param bookingId - Unique booking identifier
   * @returns Promise resolving to booking details with class and studio info
   */
  async getBookingNew(bookingId: string): Promise<BookingV2> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'performance',
      path: `/v1/bookings/${bookingId}`,
    });

    // Transform booking data to match expected structure
    return this.transformBookingData(response);
  }

  /**
   * Gets all bookings for the member in a date range
   * 
   * @param startDate - Start date for booking range
   * @param endDate - End date for booking range
   * @param excludeCancelled - Whether to exclude cancelled bookings
   * @param removeDuplicates - Whether to remove duplicate bookings
   * @returns Promise resolving to array of booking objects
   */
  async getBookingsNew(
    startDate: Date,
    endDate: Date,
    excludeCancelled: boolean = true,
    removeDuplicates: boolean = true
  ): Promise<BookingV2[]> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'performance',
      path: '/v1/bookings/me',
      params: {
        'starts_after': startDate.toISOString(),
        'ends_before': endDate.toISOString(),
        'include_canceled': (!excludeCancelled).toString(),
        'expand': 'false',
      },
    });

    let bookings = response.items.map((item: any) => this.transformBookingData(item));

    // Remove duplicates if requested (like Python implementation)
    if (removeDuplicates) {
      const seen = new Set();
      bookings = bookings.filter((booking: any) => {
        const key = booking.booking_id;
        if (seen.has(key)) {
          return false;
        }
        seen.add(key);
        return true;
      });
    }

    return bookings;
  }

  private transformBookingData(data: any): BookingV2 {
    // Transform API response to match exact Python BookingV2 model structure
    const transformedData: BookingV2 = {
      // Required fields matching Python model exactly - updated for actual API response format
      booking_id: data.bookingId || data.id || '',
      member_uuid: data.member_id || this.memberUuid, 
      person_id: data.person_id || this.memberUuid,
      service_name: data.service_name || null,
      cross_regional: data.cross_regional || null,
      intro: data.intro || null,
      checked_in: Boolean(data.checked_in),
      canceled: Boolean(data.canceled),
      late_canceled: data.late_canceled || null,
      canceled_at: data.canceled_at || null,
      ratable: Boolean(data.ratable),
      
      // OTF Class - must match BookingV2Class exactly - updated for actual API response format
      otf_class: {
        class_uuid: data.class?.classUuid || data.class?.id || '',
        name: data.class?.name || '',
        starts_at: data.class?.startsAt || data.class?.starts_at || '',
        coach: data.class?.coach ? `${data.class.coach.firstName} ${data.class.coach.lastName}` : null,
        studio: data.class?.studio ? {
          studio_uuid: data.class.studio.studioUuid || data.class.studio.id || '',
          name: data.class.studio.name || null,
          phone_number: data.class.studio.phone_number || null,
          latitude: data.class.studio.latitude || null,
          longitude: data.class.studio.longitude || null,
          time_zone: data.class.studio.time_zone || null,
          email: data.class.studio.email || null,
          address: data.class.studio.address ? {
            address_line1: data.class.studio.address.line1 || null,
            address_line2: data.class.studio.address.line2 || null,
            city: data.class.studio.address.city || null,
            postal_code: data.class.studio.address.postal_code || null,
            state: data.class.studio.address.state || null,
            country: data.class.studio.address.country || null,
            region: null,
            country_id: null,
          } : null,
          currency_code: data.class.studio.currency_code || null,
          mbo_studio_id: data.class.studio.mbo_studio_id || null,
        } : null,
        class_id: data.class?.id || null,
        class_type: data.class?.type || null,
        starts_at_utc: data.class?.starts_at || null,
      },
      
      // Workout - should now be included with correct API parameters
      workout: data.workout ? {
        id: data.workout.performanceSummaryId || data.workout.id || '',
        performance_summary_id: data.workout.performanceSummaryId || data.workout.id || '',
        calories_burned: data.workout.caloriesBurned || data.workout.calories_burned || 0,
        splat_points: data.workout.splatPoints || data.workout.splat_points || 0,
        step_count: data.workout.stepCount || data.workout.step_count || 0,
        active_time_seconds: data.workout.activeTimeSeconds || data.workout.active_time_seconds || 0,
      } : null,
      
      // Rating fields
      coach_rating: null,
      class_rating: null,
      
      // Additional fields from Python model
      paying_studio_id: null,
      mbo_booking_id: data.mboBookingId || null,
      mbo_unique_id: data.mboUniqueId || null,
      mbo_paying_unique_id: data.mboPayingUniqueId || null,
      created_at: data.createdAt || null,
      updated_at: data.updatedAt || null,
    };
    
    return transformedData;
  }

  /**
   * Rates a completed class
   * 
   * @param classUuid - UUID of the class to rate
   * @param performanceSummaryId - Performance summary identifier
   * @param classRating - Class rating (0-3, where 0 is dismiss)
   * @param coachRating - Coach rating (0-3, where 0 is dismiss)
   */
  async rateClass(
    classUuid: string,
    performanceSummaryId: string,
    classRating: 0 | 1 | 2 | 3,
    coachRating: 0 | 1 | 2 | 3
  ): Promise<void> {
    await this.client.workoutRequest({
      method: 'POST',
      apiType: 'performance',
      path: `/v1/classes/${classUuid}/rating`,
      body: {
        performance_summary_id: performanceSummaryId,
        class_rating: classRating,
        coach_rating: coachRating,
      },
    });
  }
}