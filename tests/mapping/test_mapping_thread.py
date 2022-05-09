from server.incidents.models import Incident
from server.mapping.mapping_thread import MappingThread


def test_process_task():
    incident = Incident(id="0", name="Mapping Test")
    incident.save()

    location = incident.Location(id="0", name="Mapping Test")
    location.save()

    mapper = MappingThread()
    mapper.process_task(incident.id, location.id)

    # The mapping function should have created a new "generated" layer even
    # though we do not have any surface data.
    layers = location.Layer.find(type="generated")
    assert len(layers) > 0

    # Clean up
    location.delete()
    incident.delete()
