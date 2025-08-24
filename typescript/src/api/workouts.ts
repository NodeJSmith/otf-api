import { OtfHttpClient } from '../client/http-client';
import { StatsTime, EquipmentType, ChallengeCategory } from '../types/workout-enums';
import { Workout, BookingV2, OtfClass, Coach, StudioDetail } from 'otf-api-models';

/** Complete workout data including performance, telemetry, and class details */
export interface WorkoutWithTelemetry {
  /** Performance summary identifier */
  performance_summary_id: string;
  /** Class history UUID (same as performance_summary_id) */
  class_history_uuid: string;
  /** Booking identifier */
  booking_id: string;
  /** Class UUID for ratings */
  class_uuid?: string;
  /** Coach first name */
  coach?: string;
  /** Whether this workout can be rated */
  ratable?: boolean;
  
  /** Calories burned during workout */
  calories_burned?: number;
  /** Splat points earned */
  splat_points?: number;
  /** Step count during workout */
  step_count?: number;
  /** Active workout time in seconds */
  active_time_seconds?: number;
  
  /** Time spent in each heart rate zone */
  zone_time_minutes?: ZoneTimeMinutes;
  /** Heart rate metrics */
  heart_rate?: HeartRate;
  
  /** Rower performance data */
  rower_data?: any;
  /** Treadmill performance data */
  treadmill_data?: any;
  
  /** Class information from booking */
  otf_class: OtfClass;
  /** Studio information */
  studio: StudioDetail;
  /** Telemetry data (heart rate over time) */
  telemetry?: any;
  
  /** Class rating */
  class_rating?: any;
  /** Coach rating */
  coach_rating?: any;
}

/** Heart rate zone time distribution in minutes */
export interface ZoneTimeMinutes {
  /** Time spent in gray zone (resting) */
  gray: number;
  /** Time spent in blue zone (base pace) */
  blue: number;
  /** Time spent in green zone (push pace) */
  green: number;
  /** Time spent in orange zone (all out) */
  orange: number;
  /** Time spent in red zone (max effort) */
  red: number;
}

/** Heart rate metrics for a workout */
export interface HeartRate {
  /** Maximum heart rate achieved */
  max_hr: number;
  /** Peak heart rate during workout */
  peak_hr: number;
  /** Peak heart rate as percentage of max */
  peak_hr_percent: number;
  /** Average heart rate during workout */
  avg_hr: number;
  /** Average heart rate as percentage of max */
  avg_hr_percent: number;
}

export interface PerformanceMetric {
  display_value: any;
  display_unit: string;
  metric_value: number;
}

export interface BaseEquipment {
  avg_pace: PerformanceMetric;
  avg_speed: PerformanceMetric;
  max_pace: PerformanceMetric;
  max_speed: PerformanceMetric;
  moving_time: PerformanceMetric;
  total_distance: PerformanceMetric;
}

export interface Treadmill extends BaseEquipment {
  avg_incline: PerformanceMetric;
  elevation_gained: PerformanceMetric;
  max_incline: PerformanceMetric;
}

export interface Rower extends BaseEquipment {
  avg_cadence: PerformanceMetric;
  avg_power: PerformanceMetric;
  max_cadence: PerformanceMetric;
}

export interface BodyCompositionData {
  member_uuid: string;
  scan_date: string;
  weight: number;
  body_fat_percent: number;
  muscle_mass: number;
  // Add other body composition fields as needed
}

export interface ChallengeTracker {
  programs: any[];
  challenges: any[];
  benchmarks: any[];
}

export interface LifetimeStats {
  calories: number;
  splat_point: number;
  total_black_zone: number;
  total_blue_zone: number;
  total_green_zone: number;
  total_orange_zone: number;
  total_red_zone: number;
  workout_duration: number;
  step_count: number;
}

/**
 * API for workout data, statistics, and challenge tracking
 * 
 * Provides access to workout history, performance summaries, telemetry data,
 * equipment statistics, and challenge information. Combines data from multiple
 * OTF API endpoints to provide comprehensive workout insights.
 */
export class WorkoutsApi {
  private otfInstance: any; // Will be set after initialization
  
  constructor(private client: OtfHttpClient, private memberUuid: string) {}
  
  setOtfInstance(otf: any): void {
    this.otfInstance = otf;
  }

  /**
   * Gets member's body composition scan history
   * 
   * @returns Promise resolving to array of body composition data
   */
  async getBodyCompositionList(): Promise<BodyCompositionData[]> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'default',
      path: `/member/members/${this.memberUuid}/body-composition`,
    });

    // Transform the response data to match Python model structure
    return response.data.map((item: any) => ({
      member_uuid: item.memberUUId,
      scan_date: item.scanDate,
      weight: item.weight,
      body_fat_percent: item.bodyFatPercent,
      muscle_mass: item.muscleMass,
      // Add other transformations as needed
    }));
  }

  /**
   * Gets member's challenge tracking information
   * 
   * @returns Promise resolving to challenge tracker data
   */
  async getChallengeTracker(): Promise<ChallengeTracker> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'default',
      path: `/challenges/v3.1/member/${this.memberUuid}`,
    });

    // Return the Dto part like Python implementation
    return response.Dto;
  }

  /**
   * Gets member's lifetime workout statistics
   * 
   * @param selectTime - Time period for statistics (defaults to all time)
   * @returns Promise resolving to lifetime statistics
   */
  async getMemberLifetimeStats(selectTime: StatsTime = StatsTime.AllTime): Promise<any> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'default',
      path: `/performance/v2/${this.memberUuid}/over-time/${selectTime}`,
    });

    return response.data;
  }

  /**
   * Gets member's out-of-studio workout history
   * 
   * @returns Promise resolving to array of out-of-studio workouts
   */
  async getOutOfStudioWorkoutHistory(): Promise<any[]> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'default',
      path: `/member/members/${this.memberUuid}/out-of-studio-workout`,
    });

    return response.data;
  }

  /**
   * Gets member's benchmark performances
   * 
   * @param challengeCategoryId - Challenge category filter (0 for all)
   * @param equipmentId - Equipment type filter (0 for all)
   * @param challengeSubcategoryId - Challenge subcategory filter (0 for all)
   * @returns Promise resolving to array of benchmark data
   */
  async getBenchmarks(
    challengeCategoryId: number = 0,
    equipmentId: EquipmentType | 0 = 0,
    challengeSubcategoryId: number = 0
  ): Promise<any[]> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'default',
      path: `/challenges/v3/member/${this.memberUuid}/benchmarks`,
      params: {
        equipmentId: equipmentId,
        challengeTypeId: challengeCategoryId,
        challengeSubTypeId: challengeSubcategoryId,
      },
    });

    return response.Dto;
  }

  async getChallengeTrackerDetail(challengeCategoryId: number): Promise<any[]> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'default',
      path: `/challenges/v1/member/${this.memberUuid}/participation`,
      params: {
        challengeTypeId: challengeCategoryId,
      },
    });

    return response.Dto;
  }

  // Performance Summary API methods
  async getPerformanceSummaries(limit?: number): Promise<any> {
    const params = limit ? { limit } : {};
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'performance',
      path: '/v1/performance-summaries',
      params,
    });

    return response;
  }

  /**
   * Gets performance summary for a specific workout
   * 
   * @param performanceSummaryId - Performance summary identifier
   * @returns Promise resolving to performance summary with metrics
   */
  async getPerformanceSummary(performanceSummaryId: string): Promise<any> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'performance',
      path: `/v1/performance-summaries/${performanceSummaryId}`,
    });

    return response;
  }

  // Telemetry API methods
  /**
   * Gets telemetry data for a workout
   * 
   * @param performanceSummaryId - Performance summary identifier
   * @param maxDataPoints - Maximum number of data points to retrieve
   * @returns Promise resolving to array of telemetry data points
   */
  async getTelemetry(performanceSummaryId: string, maxDataPoints: number = 150): Promise<any[]> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'telemetry',
      path: '/v1/performance/summary',
      params: {
        classHistoryUuid: performanceSummaryId,
        maxDataPoints: maxDataPoints,
      },
    });

    return response;
  }

  async getHrHistory(): Promise<any[]> {
    const response = await this.client.workoutRequest<any>({
      method: 'GET',
      apiType: 'telemetry',
      path: '/v1/physVars/maxHr/history',
      params: {
        memberUuid: this.memberUuid,
      },
    });

    return response.history;
  }

  // Helper methods for concurrent requests (simplified for now)
  async getPerformanceSummariesConcurrent(performanceSummaryIds: string[]): Promise<Record<string, any>> {
    const promises = performanceSummaryIds.map(id => 
      this.getPerformanceSummary(id).then(data => ({ id, data }))
    );
    
    const results = await Promise.all(promises);
    return results.reduce((acc, { id, data }) => {
      acc[id] = data;
      return acc;
    }, {} as Record<string, any>);
  }

  async getTelemetryConcurrent(performanceSummaryIds: string[], maxDataPoints: number = 150): Promise<Record<string, any>> {
    const promises = performanceSummaryIds.map(id => 
      this.getTelemetry(id, maxDataPoints).then(data => ({ id, data }))
    );
    
    const results = await Promise.all(promises);
    return results.reduce((acc, { id, data }) => {
      acc[id] = data;
      return acc;
    }, {} as Record<string, any>);
  }

  /**
   * Gets member's workout history with complete performance data and telemetry
   * 
   * This method combines data from multiple endpoints to create comprehensive workout objects
   * that include performance metrics, telemetry data, class details, and ratings - matching
   * the data shown in the OTF mobile app.
   * 
   * @param startDate - Start date for workout range (defaults to 30 days ago)
   * @param endDate - End date for workout range (defaults to today)
   * @param maxDataPoints - Maximum telemetry data points per workout (defaults to 150)
   * @returns Promise resolving to array of complete workout objects with telemetry
   */
  async getWorkouts(
    startDate?: Date | string,
    endDate?: Date | string,
    maxDataPoints: number = 150
  ): Promise<WorkoutWithTelemetry[]> {
    // Set default date range (30 days ago to today, like Python)
    const start = startDate 
      ? (typeof startDate === 'string' ? new Date(startDate) : startDate)
      : new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    
    const end = endDate
      ? (typeof endDate === 'string' ? new Date(endDate) : endDate)
      : new Date();

    // Get bookings from BookingsApi (requires implementation)
    const bookings = await this.getBookingsForWorkouts(start, end);
    
    // Filter out future bookings
    const now = new Date();
    const filteredBookings = bookings.filter(b => 
      !b.otf_class?.starts_at || new Date(b.otf_class.starts_at) <= now
    );

    // Extract performance summary IDs
    const performanceSummaryIds = filteredBookings
      .map(b => (b.workout as any)?.performance_summary_id)
      .filter(Boolean) as string[];

    // Get performance summaries and telemetry concurrently
    const [performanceSummaries, telemetryData] = await Promise.all([
      this.getPerformanceSummariesConcurrent(performanceSummaryIds),
      this.getTelemetryConcurrent(performanceSummaryIds, maxDataPoints),
    ]);

    // Assemble workout objects combining all data sources
    const workouts = [];
    for (const booking of filteredBookings) {
      const perfSummaryId = (booking.workout as any)?.performance_summary_id;
      if (!perfSummaryId) continue;

      const perfSummary = performanceSummaries[perfSummaryId] || {};
      const telemetry = telemetryData[perfSummaryId] || null;

      const workout = this.assembleWorkout(booking, perfSummary, telemetry);
      workouts.push(workout);
    }

    return workouts;
  }

  /**
   * Gets bookings for workout date range
   * 
   * @param startDate - Start date for booking range
   * @param endDate - End date for booking range
   * @returns Promise resolving to array of booking objects
   */
  private async getBookingsForWorkouts(startDate: Date, endDate: Date): Promise<BookingV2[]> {
    if (!this.otfInstance?.bookings) {
      console.warn('BookingsApi not available - returning empty workouts array');
      return [];
    }
    
    try {
      return await this.otfInstance.bookings.getBookingsNew(
        startDate,
        endDate,
        true, // excludeCancelled
        true  // removeDuplicates
      );
    } catch (error) {
      console.warn('Failed to get bookings for workouts:', error instanceof Error ? error.message : String(error));
      return [];
    }
  }

  /**
   * Assembles complete workout data from booking, performance summary, and telemetry
   * 
   * @param booking - Booking data with class and studio info
   * @param performanceSummary - Performance metrics and equipment data
   * @param telemetry - Heart rate telemetry over time
   * @returns Complete workout object matching Python implementation
   */
  private assembleWorkout(booking: any, performanceSummary: any, telemetry: any): WorkoutWithTelemetry {
    // Assemble workout data like Python Workout.create() method
    return {
      performance_summary_id: performanceSummary.id || 'unknown',
      class_history_uuid: performanceSummary.id || 'unknown',
      booking_id: booking.booking_id,
      class_uuid: booking.otf_class?.class_uuid || null,
      coach: booking.otf_class?.coach?.first_name || null,
      ratable: booking.ratable,
      
      // Performance metrics from performance summary
      calories_burned: performanceSummary.details?.calories_burned,
      splat_points: performanceSummary.details?.splat_points,
      step_count: performanceSummary.details?.step_count,
      zone_time_minutes: performanceSummary.details?.zone_time_minutes,
      heart_rate: performanceSummary.details?.heart_rate,
      active_time_seconds: booking.workout?.active_time_seconds,
      
      // Equipment data
      rower_data: performanceSummary.details?.equipment_data?.rower,
      treadmill_data: performanceSummary.details?.equipment_data?.treadmill,
      
      // Ratings
      class_rating: booking.class_rating,
      coach_rating: booking.coach_rating,
      
      // Related objects
      otf_class: booking.otf_class,
      studio: booking.otf_class?.studio,
      telemetry: telemetry,
    };
  }

  // Helper methods that match Python API
  async getBenchmarksByEquipment(equipmentId: EquipmentType): Promise<any[]> {
    const benchmarks = await this.getBenchmarks(0, equipmentId, 0);
    return benchmarks.filter((b: any) => b.equipment_id === equipmentId);
  }

  async getBenchmarksByChallenge(challengeCategoryId: number): Promise<any[]> {
    const benchmarks = await this.getBenchmarks(challengeCategoryId, 0, 0);
    return benchmarks.filter((b: any) => b.challenge_category_id === challengeCategoryId);
  }

  /**
   * Gets a complete workout object from a booking ID or booking object
   * 
   * @param booking - Booking ID string or booking object
   * @returns Promise resolving to complete workout with telemetry data
   */
  async getWorkoutFromBooking(booking: string | BookingV2): Promise<WorkoutWithTelemetry> {
    const bookingId = typeof booking === 'string' ? booking : booking.id;
    
    if (!this.otfInstance?.bookings) {
      throw new Error('BookingsApi not available');
    }
    
    const bookingData = await this.otfInstance.bookings.getBookingNew(bookingId);
    
    if (!bookingData.workout?.performance_summary_id) {
      throw new Error(`Workout for booking ${bookingId} not found`);
    }
    
    const [performanceSummary, telemetry] = await Promise.all([
      this.getPerformanceSummary(bookingData.workout.performance_summary_id),
      this.getTelemetry(bookingData.workout.performance_summary_id),
    ]);
    
    return this.assembleWorkout(bookingData, performanceSummary, telemetry);
  }

  /**
   * Rates a workout's class and coach
   * 
   * @param workout - Workout object to rate
   * @param classRating - Class rating (0-3, where 0 is dismiss)
   * @param coachRating - Coach rating (0-3, where 0 is dismiss)
   * @returns Promise resolving to rating confirmation
   */
  async rateClassFromWorkout(
    workout: WorkoutWithTelemetry,
    classRating: 0 | 1 | 2 | 3,
    coachRating: 0 | 1 | 2 | 3
  ): Promise<any> {
    if (!workout.ratable || !workout.class_uuid) {
      throw new Error(`Workout ${workout.performance_summary_id} is not rateable`);
    }
    
    if (workout.class_rating !== null || workout.coach_rating !== null) {
      throw new Error(`Workout ${workout.performance_summary_id} already rated`);
    }
    
    if (!this.otfInstance?.bookings) {
      throw new Error('BookingsApi not available');
    }
    
    await this.otfInstance.bookings.rateClass(
      workout.class_uuid,
      workout.performance_summary_id,
      classRating,
      coachRating
    );
    
    return this.getWorkoutFromBooking(workout.booking_id);
  }
}