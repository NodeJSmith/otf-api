export class OtfError extends Error {
  constructor(message: string, public cause?: Error) {
    super(message);
    this.name = 'OtfError';
  }
}

export class OtfRequestError extends OtfError {
  constructor(
    message: string,
    cause?: Error,
    public request?: Request,
    public response?: Response
  ) {
    super(message, cause);
    this.name = 'OtfRequestError';
  }
}

export class RetryableOtfRequestError extends OtfRequestError {
  constructor(message: string, cause?: Error, request?: Request, response?: Response) {
    super(message, cause, request, response);
    this.name = 'RetryableOtfRequestError';
  }
}

export class BookingError extends OtfError {
  constructor(message: string, cause?: Error) {
    super(message, cause);
    this.name = 'BookingError';
  }
}

export class AlreadyBookedError extends BookingError {
  constructor(message = 'Class is already booked') {
    super(message);
    this.name = 'AlreadyBookedError';
  }
}

export class BookingAlreadyCancelledError extends BookingError {
  constructor(message = 'Booking was already cancelled') {
    super(message);
    this.name = 'BookingAlreadyCancelledError';
  }
}

export class ConflictingBookingError extends BookingError {
  constructor(message = 'Conflicting booking exists') {
    super(message);
    this.name = 'ConflictingBookingError';
  }
}

export class OutsideSchedulingWindowError extends OtfError {
  constructor(message = 'Class is outside scheduling window') {
    super(message);
    this.name = 'OutsideSchedulingWindowError';
  }
}

export class ResourceNotFoundError extends OtfError {
  constructor(message = 'Resource not found') {
    super(message);
    this.name = 'ResourceNotFoundError';
  }
}

export class NoCredentialsError extends OtfError {
  constructor(message = 'No credentials available') {
    super(message);
    this.name = 'NoCredentialsError';
  }
}