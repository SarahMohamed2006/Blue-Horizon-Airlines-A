from pydantic import BaseModel, Field, ConfigDict


class CancelFlightInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    flight_id: int = Field(
        gt=0,
        description="Unique flight identifier"
    )

    employee_id: int = Field(
        gt=0,
        description="Operations Manager performing the cancellation"
    )

    reason: str = Field(
        min_length=10,
        max_length=500,
        description="Operational reason for cancelling the flight"
    )
class AssignAircraftInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flight_id: int = Field(gt=0, description="Flight ID")
    aircraft_id: int = Field(gt=0, description="Available aircraft ID")
    employee_id: int = Field(gt=0, description="Authorized employee ID")


class AssignBackupCrewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flight_id: int = Field(gt=0, description="Flight ID")
    crew_id: int = Field(gt=0, description="Backup crew member ID")
    employee_id: int = Field(gt=0, description="Authorized employee ID")