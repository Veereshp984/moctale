import { useEffect, useRef, useState } from 'react'
import { ArrowRight, BadgeCheck, KeyRound } from 'lucide-react'

import { Button } from '@/components/ui/Button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card'
import { Loader } from '@/components/ui/Loader'
import { Modal } from '@/components/ui/Modal'

const AuthPage = () => {
  const [isSending, setIsSending] = useState(false)
  const [isModalOpen, setModalOpen] = useState(false)
  const pendingTimeout = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (pendingTimeout.current !== null) {
        window.clearTimeout(pendingTimeout.current)
      }
    }
  }, [])

  const handleRequestAccess = () => {
    setIsSending(true)
    const timeout = window.setTimeout(() => {
      setIsSending(false)
      setModalOpen(true)
      pendingTimeout.current = null
    }, 900)
    pendingTimeout.current = timeout
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1.15fr_1fr]">
      <section className="space-y-6">
        <header className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Authentication
          </p>
          <h1 className="text-3xl font-semibold lg:text-4xl">Access your creative hub</h1>
          <p className="max-w-xl text-base text-muted-foreground">
            Use your verified email address to receive a secure sign-in link. New curators can request
            access and we&apos;ll guide you through onboarding.
          </p>
        </header>

        <Card className="p-8">
          <CardHeader>
            <CardTitle>Request a magic link</CardTitle>
            <CardDescription>
              Enter the email you used when applying to become a curator. We&apos;ll send you a one-time link
              to access the studio.
            </CardDescription>
          </CardHeader>
          <CardContent className="mt-6 grid gap-5">
            <label className="grid gap-2 text-sm font-medium">
              Email address
              <input
                type="email"
                inputMode="email"
                placeholder="you@example.com"
                className="h-12 rounded-xl border border-border bg-background px-4 text-base shadow-inner transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
              />
            </label>
            <label className="grid gap-2 text-sm font-medium">
              Creative discipline
              <input
                type="text"
                placeholder="Mix curator, DJ, composer"
                className="h-12 rounded-xl border border-border bg-background px-4 text-base shadow-inner transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
              />
            </label>
            <Button type="button" className="justify-between" onClick={handleRequestAccess} disabled={isSending}>
              {isSending ? 'Sending secure link' : 'Send secure link'}
              {isSending ? <Loader size="sm" className="ml-2" /> : <ArrowRight className="h-4 w-4" />}
            </Button>
          </CardContent>
          <CardFooter className="flex-col items-start gap-2 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-2 text-sm font-medium text-foreground">
              <BadgeCheck className="h-4 w-4 text-accent" />
              Access granted in under 24 hours
            </span>
            We&apos;ll never share your information. Already have a passkey?{' '}
            <button type="button" className="font-semibold text-primary underline-offset-4 hover:underline">
              Verify here
            </button>
          </CardFooter>
        </Card>
      </section>

      <aside className="space-y-6">
        <Card className="overflow-hidden bg-gradient-to-br from-primary to-accent text-primary-foreground">
          <CardHeader>
            <CardTitle className="text-primary-foreground">Passkey compatible</CardTitle>
            <CardDescription className="text-primary-foreground/70">
              Secure your account with hardware keys or biometric authentication.
            </CardDescription>
          </CardHeader>
          <CardContent className="mt-8 space-y-4 text-primary-foreground/80">
            <p className="text-base">
              We natively support WebAuthn. Configure a passkey and sign in without needing email links.
            </p>
            <div className="flex items-center gap-3 rounded-2xl bg-primary/20 px-4 py-3 text-sm font-medium">
              <KeyRound className="h-5 w-5" />
              Trusted hardware and biometric authentication
            </div>
          </CardContent>
          <CardFooter>
            <Button variant="outline" className="border-primary/40 bg-primary/10 text-primary-foreground">
              Configure passkey
            </Button>
            <span className="text-xs uppercase tracking-widest text-primary-foreground/70">
              Security first
            </span>
          </CardFooter>
        </Card>

        <Card className="p-8">
          <CardHeader>
            <CardTitle>Just exploring?</CardTitle>
            <CardDescription>
              Use our curated demo profile to explore the interface and playlist tooling.
            </CardDescription>
          </CardHeader>
          <CardContent className="mt-6 space-y-3">
            <p className="text-base text-muted-foreground">
              Sign in with the demo account to try the collaboration features and fine-tune your navigation.
            </p>
            <Button variant="secondary">Launch demo workspace</Button>
          </CardContent>
        </Card>
      </aside>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setModalOpen(false)}
        title="Secure link sent"
        description="Check your inbox for a one-time authentication link. It expires in 15 minutes."
      >
        <p>
          When you receive your magic link, open it on this device to continue seamlessly. If you requested
          access, we&apos;ll email you once your curator profile has been approved.
        </p>
        <div className="flex flex-wrap gap-2 pt-2">
          <Button onClick={() => setModalOpen(false)}>Return to studio</Button>
          <Button variant="ghost" onClick={() => setModalOpen(false)}>
            Resend link
          </Button>
        </div>
      </Modal>
    </div>
  )
}

export default AuthPage
