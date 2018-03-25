var TRK = TRK || {};
TRK.gameplay = function(game) {};

TRK.gameplay.prototype = {
    init: function() {
        this.game.input.maxPointers = 1;
        this.game.stage.disableVisibilityChange = true;
        this.score = 0;
        this.speed = 100;
        this.jumpForce = 0;
        this.dash = false;
        this.dashSpeed = 300;
    },

    preload: function() {
        this.load.image('background', 'assets/background.png');
        this.load.image('soil_ground', 'assets/soil_ground.png'); //800x14
        this.load.spritesheet('racer', 'assets/racer.png', 128, 128, 6);

    },

    create: function() {
        this.background = this.add.tileSprite(0, 0, 1600, 640, 'background');
        this.player = this.add.sprite(200, 590, 'racer');
        this.player.animations.add("ride", [0, 1, 2, 3], 4, true, true);
        this.player.animations.add("jump", [4], 4, false, true);
        this.player.animations.add("fall", [5], 4, false, true);

        // this.world.setBounds(0, 0, 1600, 640);
        this.physics.startSystem(Phaser.Physics.ARCADE);
        this.physics.enable(this.player);
        this.player.body.gravity.y = 1400
        this.player.body.collideWorldBounds = true;
        this.player.anchor.set(0.5, 1)
        // this.platforms = this.add.group();
        // this.platforms.enableBody = true;
        this.ground = this.add.tileSprite(0, 590, 1600, 14, 'soil_ground');
        this.physics.enable(this.ground);
        this.ground.body.immovable = true;
        //this.ground.autoScroll(-150, 0);

        // platforms.create(512, 600, 'soil_ground').scale.setTo(2,2).refreshBody();
        // this.ground = this.add.tileSprite(512, 600, 1440, 14, 'soil_ground').scale.setTo(2,2);
        cursors = this.input.keyboard.createCursorKeys();
        this.text = this.add.text(10, 20, this.score);
        // this.state.start()
    },



    update: function() {
        this.text.destroy();
        this.text = this.add.text(10, 20, this.score);
        this.physics.arcade.collide(this.player, this.ground);
        this.move();
        if (cursors.right.isDown) {
            this.dash = true;
        } else if (this.dash && !cursors.right.isDown) {
            this.dash = false;
        }
        if ((cursors.up.isDown || this.input.keyboard.isDown(Phaser.KeyCode.SPACEBAR)) && this.player.body.touching.down) {
            this.jumpForce += 30;
        } else if (this.player.body.touching.down && this.jumpForce > 0) {
            this.player.body.velocity.y = -this.jumpForce;
            this.jumpForce = 0;
        }
        if (this.player.body.velocity.y < -50 && !this.player.body.touching.down) {
            this.player.animations.play('jump');
        } else if (this.player.body.velocity.y > 0 && !this.player.body.touching.down) {
            this.player.animations.play('fall');
        }

    },

    move: function() {
        this.player.animations.play('ride', this.speed / 50, false);
        this.background.autoScroll(-this.currentSpeed() / 2, 0);
        this.ground.autoScroll(-this.currentSpeed(), 0);
        this.score++;
        this.speed += this.score / 3000;
    },

    stop: function() {
        this.background.stopScroll();
        this.ground.stopScroll();
        this.player.animations.play('ride');
        this.player.animations.stop('ride');
    },

    currentSpeed: function() {
        return this.speed + (this.dash ? this.dashSpeed : 0);
    },

};