import ThemeToggle from '../components/ThemeToggle'

export default function LawyerProfilePage() {
  return (
    <div className="flex-1 overflow-y-auto px-5 py-7 md:px-8">
      <h1 className="font-heading text-2xl font-extrabold md:text-[28px]">My profile</h1>
      <div className="mt-1 text-sm text-muted">This is what clients see when they find you</div>
      <div className="mt-5">
        <ThemeToggle />
      </div>

      <div className="mt-5 max-w-[640px] rounded-[22px] border border-line bg-surface p-[26px]">
        <div className="flex items-center gap-[18px]">
          <div className="flex h-[68px] w-[68px] flex-none items-center justify-center rounded-full bg-primary text-[22px] font-bold text-primary-foreground">
            MK
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2.5">
              <div className="font-heading text-xl font-extrabold">Adv. Meera Krishnan</div>
              <div className="rounded-full bg-success-bg px-2.5 py-1 text-[11px] font-bold text-success-text">
                ✓ Bar Council verified
              </div>
            </div>
            <div className="mt-1 text-[13px] text-muted">
              Criminal Law · 12 years · English, Tamil · Chennai
            </div>
          </div>
          <button className="rounded-full border border-line bg-surface px-[18px] py-2.5 text-[13px] font-semibold">
            Edit
          </button>
        </div>
        <div className="my-5 h-px bg-line" />
        <div className="text-sm leading-[1.65] text-body3">
          12 years defending clients across Chennai's sessions and High Court. Specialist in theft,
          cheating (§420) and bail matters. Known for clear, jargon-free advice — most first consults end
          with a concrete action plan.
        </div>
        <div className="mt-5 grid grid-cols-3 gap-3">
          <div className="rounded-2xl bg-bg p-3.5">
            <div className="text-lg font-extrabold">★ 4.9</div>
            <div className="mt-0.5 text-[11px] text-muted">312 reviews</div>
          </div>
          <div className="rounded-2xl bg-bg p-3.5">
            <div className="text-lg font-extrabold">₹500</div>
            <div className="mt-0.5 text-[11px] text-muted">first consult · you get ₹350</div>
          </div>
          <div className="rounded-2xl bg-bg p-3.5">
            <div className="text-lg font-extrabold">61</div>
            <div className="mt-0.5 text-[11px] text-muted">consults this month</div>
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between rounded-2xl bg-success-bg px-4 py-3.5">
          <div className="text-[13px] font-semibold text-success-dark">
            Bar Council reg: TN/1123/2014 · KYC complete · Payouts to meera@okaxis
          </div>
        </div>
      </div>
    </div>
  )
}
