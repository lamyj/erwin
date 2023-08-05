import subprocess
import spire

class Tractography(spire.TaskFactory):
    def __init__(self, fod, algorithm, seeding, target):
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = [fod]
        self.targets = [target]
        
        seeding_method, seeding_arguments = seeding[0], seeding[1:]
        
        seeding_mask = None
        seeding_count = None
        if seeding_method in ["image", "grid_per_voxel", "random_per_voxel"]:
            seeding_mask, seeding_count = seeding_arguments
            self.file_dep.append(seeding_mask)
        elif seeding_method == "dynamic":
            seeding_count, = seeding_arguments
        else:
            raise Exception(f"Unknown seeding method: {seeding_method!r}")
        
        self.actions = [(
            Tractography.action, (
                fod, algorithm, seeding_method, seeding_count, seeding_mask,
                target))]
    
    @staticmethod
    def action(
            fod, algorithm, seeding_method, seeding_count, seeding_mask, target):
        command = ["tckgen", "-force", "-algorithm", algorithm, fod, target]
        if seeding_method in ["image", "dynamic"]:
            command.extend(["-select", str(seeding_count)])
            command.extend([
                f"-seed_{seeding_method}", 
                {"image": seeding_mask, "dynamic": fod}[seeding_method]])
        else:
            command.extend([
                f"-seed_{seeding_method}", seeding_mask, str(seeding_count)])
        
        subprocess.check_call(command)
