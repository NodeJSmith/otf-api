import { BookingV2 } from 'otf-api-models';
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
        'starts-after': startDate.toISOString(),
        'ends-before': endDate.toISOString(),
        'exclude-cancelled': excludeCancelled.toString(),
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
    // Transform camelCase API response to snake_case model fields
    // This matches the Python BookingV2 model structure
    return {
      id: data.bookingId || data.id,
      class_uuid: data.classUuid || data.class?.classUuid || '',
      member_uuid: this.memberUuid,
      studio_uuid: data.studioUuid || data.class?.studio?.studioUuid || '',
      checkin_time: data.checkinTime,
      is_intro: data.isIntro || false,
      is_waitlisted: data.isWaitlisted || false,
      waitlist_position: data.waitlistPosition,
      
      // Nested objects
      otf_class: data.class ? {
        class_uuid: data.class.classUuid,
        name: data.class.name,
        starts_at: data.class.startsAt,
        ends_at: data.class.endsAt,
        coach: data.class.coach ? {
          first_name: data.class.coach.firstName,
          last_name: data.class.coach.lastName,
        } : null,
        studio: data.class.studio ? {
          studio_uuid: data.class.studio.studioUuid,
          studio_name: data.class.studio.studioName,
        } : null,
      } : {
        class_uuid: '',
        name: '',
        starts_at: '',
        ends_at: '',
        coach: null,
        studio: null,
      },
      
      workout: data.workout ? {
        id: data.workout.id,
        performance_summary_id: data.workout.performanceSummaryId,
        active_time_seconds: data.workout.activeTimeSeconds,
      } : undefined,
      
      // Additional fields from Python model
      starts_at: data.startsAt,
      ends_at: data.endsAt,
      status: data.status,
      ratable: data.ratable,
      class_rating: data.classRating,
      coach_rating: data.coachRating,
    } as any;
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