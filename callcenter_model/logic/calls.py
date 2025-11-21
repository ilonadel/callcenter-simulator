from dataclasses import dataclass

@dataclass
class IncomingCall:

    ident: int
    origin: int       
    emergency: bool   
    born_at: float    
    duration: float   

    @property
    def cid(self) -> int:
        return self.ident

    def __str__(self):
        tag = "E" if self.emergency else "N"
        return f"<Call {self.ident} [{tag}] src={self.origin} t={self.born_at:.2f} d={self.duration:.2f}>"
