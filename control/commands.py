"""Offline command identities. Numeric tolerance is a simulator policy, not hardware proof."""
from dataclasses import dataclass, asdict
import math

@dataclass(frozen=True)
class Command:
    command_id: str
    cycle_id: str
    action: str
    target: float
    issued_at: float

class CommandLifecycle:
    def __init__(self):
        self.command=None;self.accepted=False;self.last_sample=-1;self.complete=False;self.issued_ids=set()
    def issue(self, command):
        if command.command_id in self.issued_ids:
            raise ValueError('duplicate_command')
        self.issued_ids.add(command.command_id)
        self.command=command;self.accepted=False;self.complete=False;self.last_sample=-1
    def observe(self, ack):
        # Completion is terminal evidence for this immutable command. Physical
        # arrival can be sampled later; silence or later status cannot revoke it.
        if self.complete:return True
        if not isinstance(ack,dict) or self.command is None:return False
        required={'cycle_id','accepted_id','completed_id','actual_position','in_tolerance','sample_id'}
        if not required.issubset(ack):return False
        if type(ack['in_tolerance']) is not bool:return False
        if ack['completed_id'] is not None and type(ack['completed_id']) is not str:return False
        c=self.command
        sample=ack.get('sample_id')
        if type(sample) is not int or sample<=self.last_sample:return False
        if ack.get('cycle_id')!=c.cycle_id or ack.get('accepted_id')!=c.command_id:return False
        actual=ack.get('actual_position')
        if type(actual) not in (int,float):return False
        try:
            if not math.isfinite(actual):return False
        except OverflowError:
            return False
        self.last_sample=sample
        previously_accepted=self.accepted;self.accepted=True
        # Acceptance and completion must be separate, fresh samples. Exact target
        # is conservative until a device-specific tolerance has been selected.
        self.complete=bool(previously_accepted and ack.get('completed_id')==c.command_id and ack.get('in_tolerance') is True and actual==c.target)
        return self.complete
    def output(self):return asdict(self.command) if self.command else None
