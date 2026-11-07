// Copy for the "how the whole system works" sections of the landing page.
// Plain words for business owners; every claim matches what the system does today.

import {
  ArrowLeftRight, Ban, BadgeCheck, Bell, Bot, CreditCard, Database, FileSpreadsheet, KeyRound, LayoutDashboard,
  ListFilter, Lock, MessageSquare, MonitorSmartphone, Nfc, Phone, PlugZap, Receipt, Repeat, ScanSearch, Search,
  Server, ShieldCheck, Smartphone, UserPlus, Wallet, WifiOff, XCircle, type LucideIcon,
} from 'lucide-react'

type Item = { icon: LucideIcon; title: string; body: string }

/** One payment from tap to receipt. `where` says which part of the system does the step. */
export const journey: (Item & { where: 'Counter' | 'Hydra Pay' | 'Customer\'s phone' | 'Safaricom' })[] = [
  { icon: Nfc, where: 'Counter', title: 'The card is tapped', body: 'The reader at the counter reads the card instantly. An accidental double tap is ignored.' },
  { icon: ScanSearch, where: 'Hydra Pay', title: 'The customer is found', body: 'Hydra Pay looks up whose card it is and their price. An unknown card pops up on your dashboard, ready to register.' },
  { icon: ArrowLeftRight, where: 'Hydra Pay', title: 'In or out?', body: 'The first tap checks the customer in and charges the price. The next tap checks them out, free.' },
  { icon: Smartphone, where: "Customer's phone", title: 'The M-Pesa request pops up', body: 'For the exact price, paid to your till. With a prepaid card the price comes off the balance instead, with no PIN.' },
  { icon: KeyRound, where: "Customer's phone", title: 'The customer enters their PIN', body: 'They approve on their own phone. Nobody types a till number or an amount.' },
  { icon: BadgeCheck, where: 'Safaricom', title: 'Safaricom confirms', body: "Hydra Pay checks directly with Safaricom. Only Safaricom's answer counts, never an SMS or a screenshot." },
  { icon: Database, where: 'Hydra Pay', title: 'The sale is saved', body: 'Amount, time, card and M-Pesa code. Nothing is ever deleted: a correction is added as a new entry.' },
  { icon: Receipt, where: 'Hydra Pay', title: 'Everyone is told', body: 'The customer gets a receipt on WhatsApp, or by SMS if WhatsApp fails. Your dashboard updates live.' },
]

/** The parts of the system, in the order money and information flow. */
export const parts: Item[] = [
  { icon: CreditCard, title: 'Card, tag or wristband', body: 'One per customer. It holds only an ID number, no money and no personal details.' },
  { icon: Nfc, title: 'Reader at the counter', body: 'A small, low-cost reader plugged into a laptop. It reads each tap and passes it on.' },
  { icon: Server, title: 'Hydra Pay', body: 'Knows every card and price, sends M-Pesa requests, checks them with Safaricom and keeps the records. Runs on the laptop or in the cloud.' },
  { icon: BadgeCheck, title: 'Safaricom M-Pesa', body: "Sends the request to the customer's phone and confirms the payment. Money goes straight to your till." },
  { icon: LayoutDashboard, title: 'Your dashboard', body: 'Live money, cards, payments and history on any phone, tablet or computer.' },
  { icon: MessageSquare, title: 'WhatsApp, SMS & USSD', body: 'Receipts and alerts for customers, plus a self-service menu on any phone.' },
]

export const forCustomers: Item[] = [
  { icon: Nfc, title: 'Tap to pay', body: 'No cash, no change, no till number to type.' },
  { icon: Receipt, title: 'Receipts', body: 'Every payment with its M-Pesa code, on WhatsApp or by SMS.' },
  { icon: MessageSquare, title: 'WhatsApp menu', body: 'Send "hi" to see your card and payments, or change your phone number yourself.' },
  { icon: Bot, title: 'Help in your language', body: 'An assistant on WhatsApp that understands English, Kiswahili and Sheng, even voice notes.' },
  { icon: Phone, title: 'USSD menu, no internet needed', body: 'Card details, payments, M-Pesa top-up, statement by SMS, block a lost card, change PIN, in English or Kiswahili.' },
  { icon: Bell, title: 'Balance alerts', body: 'Prepaid customers are told when their balance is too low to tap in.' },
]

export const forOwners: Item[] = [
  { icon: LayoutDashboard, title: 'Live dashboard', body: "Today's money, paid and unpaid taps, who is inside and a live feed of every tap." },
  { icon: UserPlus, title: 'Register in seconds', body: 'Tap a new card, then enter the name, phone number and a price for that customer.' },
  { icon: Wallet, title: 'Top-ups and undo', body: 'Top up a prepaid card with M-Pesa or cash. Undo a mistake and the history is kept.' },
  { icon: Ban, title: 'Block or replace a card', body: 'Block a lost card, then move the person, balance and history to a new one.' },
  { icon: ListFilter, title: 'Search everything', body: 'Payments by name, phone or M-Pesa code, plus card taps and wallet history.' },
  { icon: FileSpreadsheet, title: 'Excel export', body: 'Download the day as a spreadsheet for your books.' },
  { icon: Bell, title: 'SMS alerts', body: 'Know when a blocked card is tapped, with an optional daily summary.' },
  { icon: Lock, title: 'Admin PIN', body: 'Every change needs your PIN, so staff can watch but not edit.' },
  { icon: MonitorSmartphone, title: 'Any screen', body: 'Phone, tablet or desktop, in light or dark mode and six colour themes.' },
]

/** What happens when things don't go to plan. */
export const whatIf: Item[] = [
  { icon: XCircle, title: 'The customer cancels or enters a wrong PIN', body: 'The sale shows as not paid. Nothing is counted as money received.' },
  { icon: WifiOff, title: 'The network is slow', body: 'The payment stays "waiting", never marked paid or failed too early. Hydra Pay keeps checking with Safaricom.' },
  { icon: Repeat, title: 'A card is tapped twice by mistake', body: 'The repeat is ignored, and a card never gets a second request while one is still waiting.' },
  { icon: CreditCard, title: 'A card is lost', body: 'Block it from the dashboard or by USSD, then move the person to a new card. Nothing is lost.' },
  { icon: Wallet, title: 'A prepaid balance is too low', body: 'The tap is refused and the customer is told their balance. An automatic M-Pesa top-up request can be switched on.' },
  { icon: Search, title: 'An unknown card is tapped', body: 'It appears on your dashboard so you can register it on the spot.' },
  { icon: Ban, title: 'A blocked card is tapped', body: 'Refused. The customer is told to see the desk and you get an SMS alert.' },
  { icon: ShieldCheck, title: 'Someone shows a fake M-Pesa SMS', body: "It changes nothing. Only Safaricom's own confirmation marks a sale as paid." },
]

export const getStarted: Item[] = [
  { icon: PlugZap, title: 'Set up the reader', body: 'Plug the reader into the laptop at your counter and start Hydra Pay.' },
  { icon: Smartphone, title: 'Connect M-Pesa', body: 'Link your M-Pesa till so payments go straight to you.' },
  { icon: UserPlus, title: 'Register customers', body: 'Tap each new card and enter the name, phone number and price.' },
  { icon: Wallet, title: 'Choose how to charge', body: 'Pay each time, or prepaid cards for regulars.' },
  { icon: Nfc, title: 'Start serving', body: 'Customers tap, pay and walk in. Watch it all live.' },
]

export const faq: [string, string][] = [
  ['Does the customer need a smartphone?', 'No. The M-Pesa request works on any phone, receipts can come by SMS, and the USSD menu works without internet.'],
  ['Where does the money go?', 'Straight to your own M-Pesa till. Hydra Pay never holds your money. With prepaid cards, customers pay your till when they top up and Hydra Pay keeps track of the balance.'],
  ['Does it cost customers anything extra?', 'No fee from Hydra Pay. Standard M-Pesa charges apply as usual.'],
  ['Can someone fake a payment?', 'No. A sale only counts when Safaricom confirms it directly to Hydra Pay. Fake SMSs and screenshots change nothing.'],
  ['Can my staff change the records?', 'Every change needs your admin PIN, and nothing is ever deleted: an undo is added as a new entry, so the full history stays.'],
  ['What is stored on the card?', 'Only an ID number. No money or personal details, so a lost card can simply be blocked and replaced.'],
  ['What if the internet goes down?', "M-Pesa needs a connection, so payments wait until it's back. Nothing is marked paid until Safaricom confirms. A reader that saves taps offline is next on our list."],
  ['Do I need to keep a laptop on?', 'The reader plugs into a laptop at the counter. Hydra Pay itself can run on that laptop or in the cloud, so you can check the dashboard from anywhere.'],
  ["Is my customers' data safe?", "Hydra Pay stores only names, phone numbers and payment records, keeps its keys out of the code and is designed in line with Kenya's Data Protection Act."],
]
