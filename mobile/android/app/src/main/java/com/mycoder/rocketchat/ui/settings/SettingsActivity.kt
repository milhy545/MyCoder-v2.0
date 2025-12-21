package com.mycoder.rocketchat.ui.settings

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.mycoder.rocketchat.R

/**
 * Settings Activity
 * (Placeholder for future settings implementation)
 */
class SettingsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        // TODO: Implement settings UI and logic
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}
