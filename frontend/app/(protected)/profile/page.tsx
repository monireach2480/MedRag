import { ScrollArea } from "@/components/ui/scroll-area"
import { ProfileView } from "@/components/profile-view"

export default function ProfilePage() {
  return (
    <ScrollArea className="h-full">
      <ProfileView />
    </ScrollArea>
  )
}
